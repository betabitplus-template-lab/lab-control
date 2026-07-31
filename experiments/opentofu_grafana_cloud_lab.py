#!/usr/bin/env python3
"""Validate an ephemeral OpenTofu lifecycle against Grafana Cloud."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


FOLDER_UID = "ternforge-opentofu-lab"
DATASOURCE_UID = "ternforge-opentofu-github-lab"
DASHBOARD_UID = "ternforge-opentofu-lab"
ALERT_UID = "ternforge-opentofu-rule-lab"
CONTACT_POINT_NAME = "Ternforge OpenTofu Lab"
PLUGIN_SLUG = "grafana-github-datasource"


class CommandError(RuntimeError):
    def __init__(self, command: list[str], returncode: int, output: str) -> None:
        super().__init__(f"command failed ({returncode}): {' '.join(command)}")
        self.output = output


def _secret_values() -> list[str]:
    names = (
        "GRAFANA_AUTH",
        "GRAFANA_CLOUD_ACCESS_POLICY_TOKEN",
        "GITHUB_APP_PRIVATE_KEY",
    )
    return [value for name in names if (value := os.environ.get(name))]


def _redact(value: str) -> str:
    redacted = value
    for secret in _secret_values():
        redacted = redacted.replace(secret, "<redacted>")
    return redacted


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    expected: set[int] | None = None,
) -> tuple[int, str]:
    expected = expected or {0}
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    output = _redact(completed.stdout)
    if completed.returncode not in expected:
        raise CommandError(command, completed.returncode, output)
    return completed.returncode, output


def _request(path: str) -> tuple[int, Any]:
    base_url = os.environ["GRAFANA_URL"].rstrip("/")
    token = os.environ["GRAFANA_AUTH"]
    request = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = _redact(raw.decode(errors="replace"))
        return exc.code, payload


def _wait(path: str, expected_status: int, timeout: int = 180) -> Any:
    deadline = time.monotonic() + timeout
    last: tuple[int, Any] | None = None
    while time.monotonic() < deadline:
        last = _request(path)
        if last[0] == expected_status:
            return last[1]
        time.sleep(5)
    raise RuntimeError(f"{path} did not reach HTTP {expected_status}; last={last}")


def _contact_point_exists() -> tuple[bool, str | None]:
    status, payload = _request("/api/v1/provisioning/contact-points")
    if status != 200 or not isinstance(payload, list):
        return False, None
    for item in payload:
        if isinstance(item, dict) and item.get("name") == CONTACT_POINT_NAME:
            return True, str(item.get("uid") or "")
    return False, None


def _wait_datasource_health(timeout: int = 180) -> tuple[dict[str, Any], float]:
    path = f"/api/datasources/uid/{DATASOURCE_UID}/health"
    started = time.monotonic()
    deadline = started + timeout
    last: tuple[int, Any] | None = None
    while time.monotonic() < deadline:
        last = _request(path)
        status, payload = last
        if status == 200 and isinstance(payload, dict) and payload.get("status") == "OK":
            return payload, round(time.monotonic() - started, 3)
        time.sleep(5)
    raise RuntimeError(f"GitHub datasource did not become healthy; last={last}")


def _verify_created() -> dict[str, Any]:
    plugin = _wait(f"/api/plugins/{PLUGIN_SLUG}/settings", 200)
    folder = _wait(f"/api/folders/{FOLDER_UID}", 200)
    datasource = _wait(f"/api/datasources/uid/{DATASOURCE_UID}", 200)
    health, health_wait_seconds = _wait_datasource_health()
    dashboard = _wait(f"/api/dashboards/uid/{DASHBOARD_UID}", 200)
    alert = _wait(f"/api/v1/provisioning/alert-rules/{ALERT_UID}", 200)
    contact_exists, contact_uid = _contact_point_exists()
    if not contact_exists:
        raise RuntimeError("contact point was not found after apply")
    panels = dashboard.get("dashboard", {}).get("panels", []) if isinstance(dashboard, dict) else []
    return {
        "plugin_version": plugin.get("info", {}).get("version") if isinstance(plugin, dict) else None,
        "folder_uid": folder.get("uid") if isinstance(folder, dict) else None,
        "datasource_uid": datasource.get("uid") if isinstance(datasource, dict) else None,
        "datasource_health": health.get("status"),
        "datasource_health_wait_seconds": health_wait_seconds,
        "dashboard_uid": dashboard.get("dashboard", {}).get("uid") if isinstance(dashboard, dict) else None,
        "dashboard_panel_count": len(panels),
        "alert_uid": alert.get("uid") if isinstance(alert, dict) else None,
        "contact_point_uid": contact_uid,
    }


def _verify_destroyed() -> dict[str, int]:
    paths = {
        "plugin": f"/api/plugins/{PLUGIN_SLUG}/settings",
        "folder": f"/api/folders/{FOLDER_UID}",
        "datasource": f"/api/datasources/uid/{DATASOURCE_UID}",
        "dashboard": f"/api/dashboards/uid/{DASHBOARD_UID}",
        "alert": f"/api/v1/provisioning/alert-rules/{ALERT_UID}",
    }
    statuses: dict[str, int] = {}
    for name, path in paths.items():
        _wait(path, 404, timeout=240)
        statuses[name] = 404
    contact_exists, _ = _contact_point_exists()
    if contact_exists:
        raise RuntimeError("contact point still exists after destroy")
    statuses["contact_point"] = 404
    return statuses


def _plan_actions(plan_json: str) -> list[dict[str, Any]]:
    payload = json.loads(plan_json)
    return [
        {
            "address": item.get("address"),
            "actions": item.get("change", {}).get("actions"),
        }
        for item in payload.get("resource_changes", [])
    ]


def _write_evidence(output_dir: Path, summary: dict[str, Any], logs: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# OpenTofu Grafana Cloud lifecycle lab",
        "",
        f"Outcome: **{summary['outcome']}**",
        "",
        f"OpenTofu: `{summary.get('opentofu_version')}`",
        f"Grafana provider: `{summary.get('grafana_provider_version')}`",
        f"Initial resources: `{summary.get('initial_resource_count')}`",
        f"No-drift plan exit code: `{summary.get('no_drift_exit_code')}`",
        f"Controlled-change plan exit code: `{summary.get('change_plan_exit_code')}`",
        f"Post-change no-drift exit code: `{summary.get('post_change_no_drift_exit_code')}`",
        f"Cleanup verified: `{summary.get('cleanup_verified')}`",
        f"Secret scan passed: `{summary.get('secret_scan_passed')}`",
        "",
        "OpenTofu state and binary plans were ephemeral runner-only files and were not uploaded.",
    ]
    if summary.get("error"):
        lines.extend(["", "## Error", "", f"`{summary['error']}`"])
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n")
    (output_dir / "opentofu.log").write_text(
        "\n\n".join(_redact(log) for log in logs) + "\n"
    )


def _secret_scan(output_dir: Path) -> bool:
    marker = "BEGIN " + "PRIVATE KEY"
    rsa_marker = "BEGIN RSA " + "PRIVATE KEY"
    for path in output_dir.rglob("*"):
        if not path.is_file():
            continue
        content = path.read_text(errors="replace")
        if any(secret in content for secret in _secret_values()):
            return False
        if marker in content or rsa_marker in content:
            return False
    return True


def validate(working_dir: Path, output_dir: Path) -> None:
    env = os.environ.copy()
    env.update({"TF_IN_AUTOMATION": "1", "TF_INPUT": "0", "CHECKPOINT_DISABLE": "1"})
    required = [
        "GRAFANA_URL",
        "GRAFANA_AUTH",
        "GRAFANA_CLOUD_ACCESS_POLICY_TOKEN",
        "TF_VAR_grafana_stack_slug",
        "TF_VAR_github_app_id",
        "TF_VAR_github_app_installation_id",
        "GITHUB_APP_PRIVATE_KEY",
    ]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise RuntimeError(f"missing required environment variables: {missing}")
    env["TF_VAR_github_data_source_secret"] = json.dumps(
        {"private" + "Key": env["GITHUB_APP_PRIVATE_KEY"]}
    )

    logs: list[str] = []
    summary: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "OpenTofu Grafana Cloud lifecycle",
        "outcome": "failed",
        "cleanup_verified": False,
        "secret_scan_passed": False,
    }
    destroyed = False
    pending_error: Exception | None = None
    try:
        _, version_output = _run(["tofu", "version", "-json"], cwd=working_dir, env=env)
        version = json.loads(version_output)
        summary["opentofu_version"] = version.get("terraform_version")
        summary["grafana_provider_version"] = "4.40.1"
        logs.append(version_output)

        for command in (
            ["tofu", "init", "-input=false", "-lockfile=readonly"],
            ["tofu", "validate", "-json"],
        ):
            _, output = _run(command, cwd=working_dir, env=env)
            logs.append(output)

        initial_plan = working_dir / "initial.tfplan"
        _, output = _run(
            ["tofu", "plan", "-input=false", "-out", str(initial_plan)],
            cwd=working_dir,
            env=env,
        )
        logs.append(output)
        _, plan_json = _run(
            ["tofu", "show", "-json", str(initial_plan)], cwd=working_dir, env=env
        )
        summary["initial_plan_actions"] = _plan_actions(plan_json)
        summary["initial_resource_count"] = len(summary["initial_plan_actions"])
        _, output = _run(
            ["tofu", "apply", "-input=false", "-auto-approve", str(initial_plan)],
            cwd=working_dir,
            env=env,
        )
        logs.append(output)
        summary["created"] = _verify_created()

        code, output = _run(
            ["tofu", "plan", "-input=false", "-detailed-exitcode"],
            cwd=working_dir,
            env=env,
            expected={0, 2},
        )
        logs.append(output)
        summary["no_drift_exit_code"] = code
        if code != 0:
            raise RuntimeError("second plan reported drift")

        change_env = env.copy()
        change_env["TF_VAR_alert_threshold_seconds"] = "900"
        change_plan = working_dir / "change.tfplan"
        code, output = _run(
            [
                "tofu",
                "plan",
                "-input=false",
                "-detailed-exitcode",
                "-out",
                str(change_plan),
            ],
            cwd=working_dir,
            env=change_env,
            expected={0, 2},
        )
        logs.append(output)
        summary["change_plan_exit_code"] = code
        if code != 2:
            raise RuntimeError("controlled threshold change was not detected")
        _, change_json = _run(
            ["tofu", "show", "-json", str(change_plan)], cwd=working_dir, env=change_env
        )
        summary["change_plan_actions"] = _plan_actions(change_json)
        changed = [
            item
            for item in summary["change_plan_actions"]
            if item["actions"] != ["no-op"]
        ]
        expected_change = [
            {"address": "grafana_rule_group.fleet_health", "actions": ["update"]}
        ]
        if changed != expected_change:
            raise RuntimeError(f"controlled change touched unexpected resources: {changed}")
        _, output = _run(
            ["tofu", "apply", "-input=false", "-auto-approve", str(change_plan)],
            cwd=working_dir,
            env=change_env,
        )
        logs.append(output)

        code, output = _run(
            ["tofu", "plan", "-input=false", "-detailed-exitcode"],
            cwd=working_dir,
            env=change_env,
            expected={0, 2},
        )
        logs.append(output)
        summary["post_change_no_drift_exit_code"] = code
        if code != 0:
            raise RuntimeError("post-change plan reported drift")

        _, state_list = _run(["tofu", "state", "list"], cwd=working_dir, env=change_env)
        summary["state_resources"] = [line for line in state_list.splitlines() if line]
        _, output = _run(
            ["tofu", "destroy", "-input=false", "-auto-approve"],
            cwd=working_dir,
            env=change_env,
        )
        logs.append(output)
        destroyed = True
        summary["destroyed"] = _verify_destroyed()
        summary["cleanup_verified"] = True
        summary["outcome"] = "passed"
    except Exception as exc:
        pending_error = exc
        summary["error"] = _redact(str(exc))
        if isinstance(exc, CommandError):
            logs.append(exc.output)
    finally:
        if not destroyed and (working_dir / "terraform.tfstate").exists():
            try:
                cleanup_env = env.copy()
                cleanup_env["TF_VAR_alert_threshold_seconds"] = "900"
                _, output = _run(
                    ["tofu", "destroy", "-input=false", "-auto-approve"],
                    cwd=working_dir,
                    env=cleanup_env,
                )
                logs.append(output)
                summary["destroyed"] = _verify_destroyed()
                summary["cleanup_verified"] = True
            except Exception as cleanup_exc:
                summary["cleanup_error"] = _redact(str(cleanup_exc))

        for path in working_dir.glob("*.tfplan"):
            path.unlink(missing_ok=True)
        for path in working_dir.glob("terraform.tfstate*"):
            path.unlink(missing_ok=True)
        shutil.rmtree(working_dir / ".terraform", ignore_errors=True)

        _write_evidence(output_dir, summary, logs)
        summary["secret_scan_passed"] = _secret_scan(output_dir)
        if not summary["secret_scan_passed"]:
            summary["outcome"] = "failed"
            summary["error"] = "secret scan found sensitive material in evidence"
            pending_error = RuntimeError(summary["error"])
        _write_evidence(output_dir, summary, logs)

    if pending_error is not None:
        raise pending_error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate(args.working_dir.resolve(), args.output_dir.resolve())
    except Exception as exc:
        print(_redact(str(exc)), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
