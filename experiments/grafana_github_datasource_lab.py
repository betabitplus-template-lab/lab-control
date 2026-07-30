#!/usr/bin/env python3
"""Validate Grafana's official GitHub data source against a personal-account fleet."""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DATASOURCE_UID = "github"
ALERT_UID = "fleet-doctor-failures"


def _request(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    auth: tuple[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode()
    request_headers = {"Accept": "application/json"}
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    if auth is not None:
        raw = f"{auth[0]}:{auth[1]}".encode()
        request_headers["Authorization"] = "Basic " + base64.b64encode(raw).decode()
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url, data=data, method=method, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw.decode(errors="replace")
        return exc.code, payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def prepare(args: argparse.Namespace) -> None:
    root = Path(args.provisioning_dir)
    datasource = {
        "apiVersion": 1,
        "datasources": [
            {
                "name": "GitHub",
                "type": "grafana-github-datasource",
                "uid": DATASOURCE_UID,
                "access": "proxy",
                "editable": False,
                "jsonData": {
                    "githubUrl": "https://api.github.com",
                    "selectedAuthType": "github-app",
                    "appId": os.environ["APP_NUMERIC_ID"],
                    "installationId": os.environ["APP_INSTALLATION_ID"],
                    "cachingEnabled": True,
                },
                "secureJsonData": {"privateKey": os.environ["APP_KEY_MATERIAL"]},
            }
        ],
    }
    alerting = {
        "apiVersion": 1,
        "groups": [
            {
                "orgId": 1,
                "name": "ternforge-github-lab",
                "folder": "Ternforge Lab",
                "interval": "10s",
                "rules": [
                    {
                        "uid": ALERT_UID,
                        "title": "Fleet Doctor failures",
                        "condition": "C",
                        "data": [
                            {
                                "refId": "A",
                                "relativeTimeRange": {"from": 1_209_600, "to": 0},
                                "datasourceUid": DATASOURCE_UID,
                                "model": {
                                    "datasource": {
                                        "type": "grafana-github-datasource",
                                        "uid": DATASOURCE_UID,
                                    },
                                    "queryType": "Workflow_Runs",
                                    "owner": args.owner,
                                    "repository": args.workflow_repository,
                                    "options": {"workflowID": args.workflow_file},
                                    "intervalMs": 1_000,
                                    "maxDataPoints": 43_200,
                                    "refId": "A",
                                },
                            },
                            {
                                "refId": "B",
                                "relativeTimeRange": {"from": 0, "to": 0},
                                "datasourceUid": "__expr__",
                                "model": {
                                    "datasource": {"type": "__expr__", "uid": "__expr__"},
                                    "type": "sql",
                                    "expression": (
                                        "SELECT COUNT(*) AS value FROM A "
                                        "WHERE conclusion = 'failure'"
                                    ),
                                    "format": "table",
                                    "intervalMs": 1_000,
                                    "maxDataPoints": 43_200,
                                    "refId": "B",
                                },
                            },
                            {
                                "refId": "C",
                                "relativeTimeRange": {"from": 0, "to": 0},
                                "datasourceUid": "__expr__",
                                "model": {
                                    "datasource": {"type": "__expr__", "uid": "__expr__"},
                                    "type": "threshold",
                                    "expression": "B",
                                    "conditions": [
                                        {
                                            "evaluator": {"params": [0], "type": "gt"},
                                            "operator": {"type": "and"},
                                            "query": {"params": ["C"]},
                                            "reducer": {"params": [], "type": "last"},
                                            "type": "query",
                                        }
                                    ],
                                    "intervalMs": 1_000,
                                    "maxDataPoints": 43_200,
                                    "refId": "C",
                                },
                            },
                        ],
                        "noDataState": "OK",
                        "execErrState": "Error",
                        "for": "0s",
                        "isPaused": False,
                        "annotations": {
                            "summary": "The selected GitHub workflow has failed runs."
                        },
                        "labels": {"component": "github-datasource-lab"},
                    }
                ],
            }
        ],
    }
    _write_json(root / "datasources" / "github.yaml", datasource)
    _write_json(root / "alerting" / "rules.yaml", alerting)
    os.chmod(root / "datasources" / "github.yaml", 0o600)
    os.chmod(root / "alerting" / "rules.yaml", 0o600)


def _frame_rows(frame: dict[str, Any]) -> list[dict[str, Any]]:
    fields = [field["name"] for field in frame.get("schema", {}).get("fields", [])]
    values = frame.get("data", {}).get("values", [])
    if not fields or len(fields) != len(values):
        return []
    count = max((len(column) for column in values), default=0)
    rows: list[dict[str, Any]] = []
    for index in range(count):
        row: dict[str, Any] = {}
        for name, column in zip(fields, values, strict=True):
            row[name] = column[index] if index < len(column) else None
        rows.append(row)
    return rows


def _query(base_url: str, model: dict[str, Any]) -> dict[str, Any]:
    now_ms = int(time.time() * 1000)
    body = {
        "from": str(now_ms - 14 * 86_400_000),
        "to": str(now_ms),
        "queries": [
            {
                **model,
                "refId": "A",
                "datasource": {
                    "type": "grafana-github-datasource",
                    "uid": DATASOURCE_UID,
                },
                "intervalMs": 1_000,
                "maxDataPoints": 43_200,
            }
        ],
    }
    started = time.monotonic()
    status, payload = _request(
        f"{base_url}/api/ds/query",
        method="POST",
        body=body,
        timeout=60,
    )
    elapsed_ms = round((time.monotonic() - started) * 1000, 1)
    result = (payload or {}).get("results", {}).get("A", {}) if isinstance(payload, dict) else {}
    frames = result.get("frames", []) if isinstance(result, dict) else []
    rows = [row for frame in frames for row in _frame_rows(frame)]
    return {
        "http_status": status,
        "elapsed_ms": elapsed_ms,
        "error": result.get("error") if isinstance(result, dict) else payload,
        "rows": rows,
    }


def _rate_limit_used(token: str) -> int | None:
    status, payload = _request(
        "https://api.github.com/rate_limit",
        headers={
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    if status != 200 or not isinstance(payload, dict):
        return None
    return payload.get("resources", {}).get("core", {}).get("used")


def _alert_observation(base_url: str, timeout_seconds: int = 120) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    observation: dict[str, Any] = {
        "rule_present": False,
        "state_endpoint": None,
        "firing": False,
        "rule_health": None,
        "rule_error": None,
    }
    while time.monotonic() < deadline:
        status, rule = _request(
            f"{base_url}/api/v1/provisioning/alert-rules/{ALERT_UID}"
        )
        observation["rule_present"] = status == 200
        if isinstance(rule, dict):
            observation["rule_health"] = rule.get("health")
            observation["rule_error"] = rule.get("error")
        for endpoint in (
            "/api/prometheus/grafana/api/v1/alerts",
            "/api/alertmanager/grafana/api/v2/alerts",
        ):
            state_status, state = _request(base_url + endpoint)
            if state_status != 200:
                continue
            observation["state_endpoint"] = endpoint
            text = json.dumps(state).lower()
            if ALERT_UID.lower() in text and (
                '"state":"firing"' in text
                or '"state": "firing"' in text
                or '"alertstate":"alerting"' in text
                or '"alertstate": "alerting"' in text
            ):
                observation["firing"] = True
                return observation
        time.sleep(5)
    return observation


def validate(args: argparse.Namespace) -> None:
    base_url = args.base_url.rstrip("/")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    status, health = _request(
        f"{base_url}/api/datasources/uid/{DATASOURCE_UID}/health",
        timeout=60,
    )
    app_token = os.environ["SCOPED_APP_TOKEN"]
    rate_before = _rate_limit_used(app_token)
    repositories_first = _query(
        base_url,
        {"queryType": "Repositories", "owner": args.owner, "repository": "", "options": {}},
    )
    rate_after_first = _rate_limit_used(app_token)
    repositories_repeat = _query(
        base_url,
        {"queryType": "Repositories", "owner": args.owner, "repository": "", "options": {}},
    )
    rate_after_repeat = _rate_limit_used(app_token)
    workflows = _query(
        base_url,
        {
            "queryType": "Workflows",
            "owner": args.owner,
            "repository": args.workflow_repository,
            "options": {"timeField": "CreatedAt", "query": ""},
        },
    )
    workflow_runs = _query(
        base_url,
        {
            "queryType": "Workflow_Runs",
            "owner": args.owner,
            "repository": args.workflow_repository,
            "options": {"workflowID": args.workflow_file, "branch": ""},
        },
    )
    pull_requests = _query(
        base_url,
        {
            "queryType": "Pull_Requests",
            "owner": args.owner,
            "repository": "",
            "options": {"query": "is:open author:app/renovate", "timeField": "None"},
        },
    )
    issues = _query(
        base_url,
        {
            "queryType": "Issues",
            "owner": args.owner,
            "repository": "",
            "options": {
                "query": "is:open label:renovate/config-error",
                "timeField": "None",
            },
        },
    )
    releases = _query(
        base_url,
        {
            "queryType": "Releases",
            "owner": args.owner,
            "repository": args.workflow_repository,
            "options": {},
        },
    )
    unselected_private = _query(
        base_url,
        {
            "queryType": "Workflows",
            "owner": args.owner,
            "repository": args.unselected_private_repository,
            "options": {"timeField": "CreatedAt", "query": ""},
        },
    )
    repo_names = {
        str(row.get("name"))
        for row in repositories_first["rows"]
        if row.get("name") is not None
    }
    workflow_failures = sum(
        1 for row in workflow_runs["rows"] if row.get("conclusion") == "failure"
    )
    selected_expected = set(args.selected_repository)
    alert = _alert_observation(base_url)
    summary = {
        "schema_version": 1,
        "grafana": {
            "health_http_status": status,
            "health_status": health.get("status") if isinstance(health, dict) else None,
            "health_message": health.get("message") if isinstance(health, dict) else None,
        },
        "github_app": {
            "owner_type": args.owner_type,
            "selected_repositories_expected": sorted(selected_expected),
            "selected_repositories_visible": sorted(selected_expected & repo_names),
            "selected_repositories_all_visible": selected_expected <= repo_names,
            "repositories_query_count": len(repo_names),
            "unselected_private_query_denied": bool(
                unselected_private["error"]
                or unselected_private["http_status"] in {401, 403, 404}
            ),
            "unselected_private_query_error_present": bool(unselected_private["error"]),
        },
        "queries": {
            "repositories": {
                "row_count": len(repositories_first["rows"]),
                "first_elapsed_ms": repositories_first["elapsed_ms"],
                "repeat_elapsed_ms": repositories_repeat["elapsed_ms"],
                "error": repositories_first["error"],
            },
            "workflows": {"row_count": len(workflows["rows"]), "error": workflows["error"]},
            "workflow_runs": {
                "row_count": len(workflow_runs["rows"]),
                "failure_count": workflow_failures,
                "error": workflow_runs["error"],
            },
            "pull_requests": {
                "row_count": len(pull_requests["rows"]),
                "error": pull_requests["error"],
            },
            "configuration_warning_issues": {
                "row_count": len(issues["rows"]),
                "error": issues["error"],
            },
            "releases": {"row_count": len(releases["rows"]), "error": releases["error"]},
        },
        "cache": {
            "core_rate_used_before": rate_before,
            "core_rate_used_after_first": rate_after_first,
            "core_rate_used_after_repeat": rate_after_repeat,
            "repeat_added_core_requests": (
                rate_after_repeat - rate_after_first
                if rate_after_repeat is not None and rate_after_first is not None
                else None
            ),
        },
        "alerting": alert,
    }
    summary["assertions"] = {
        "datasource_healthy": summary["grafana"]["health_status"] == "OK",
        "selected_repositories_visible": summary["github_app"]["selected_repositories_all_visible"],
        "workflow_runs_observed": len(workflow_runs["rows"]) > 0,
        "known_failures_observed": workflow_failures > 0,
        "alert_rule_present": alert["rule_present"],
        "alert_fired": alert["firing"],
    }
    _write_json(output_dir / "summary.json", summary)
    required = list(summary["assertions"])
    failed = [name for name in required if not summary["assertions"][name]]
    if failed:
        raise SystemExit("failed assertions: " + ", ".join(failed))


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--provisioning-dir", required=True)
    prepare_parser.add_argument("--owner", required=True)
    prepare_parser.add_argument("--workflow-repository", required=True)
    prepare_parser.add_argument("--workflow-file", required=True)
    prepare_parser.set_defaults(func=prepare)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--base-url", default="http://127.0.0.1:3000")
    validate_parser.add_argument("--output-dir", required=True)
    validate_parser.add_argument("--owner", required=True)
    validate_parser.add_argument("--owner-type", choices=("User", "Organization"), required=True)
    validate_parser.add_argument("--workflow-repository", required=True)
    validate_parser.add_argument("--workflow-file", required=True)
    validate_parser.add_argument("--unselected-private-repository", required=True)
    validate_parser.add_argument("--selected-repository", action="append", required=True)
    validate_parser.set_defaults(func=validate)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
