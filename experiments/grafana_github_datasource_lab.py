#!/usr/bin/env python3
"""Validate Grafana's official GitHub data source and installation scope."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DATASOURCE_UID = "github"


def _request(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    timeout: float = 30,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
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
                    "selectedAuthType": "github-app",
                    "appId": os.environ["APP_NUMERIC_ID"],
                    "installationId": os.environ["APP_INSTALLATION_ID"],
                    "cachingEnabled": True,
                },
                "secureJsonData": {"privateKey": os.environ["APP_KEY_MATERIAL"]},
            }
        ],
    }
    path = root / "datasources" / "github.yaml"
    _write_json(path, datasource)
    # The file exists only in the ephemeral runner, mounted read-only into Grafana.
    os.chmod(path, 0o644)


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
    result = (
        (payload or {}).get("results", {}).get("A", {})
        if isinstance(payload, dict)
        else {}
    )
    frames = result.get("frames", []) if isinstance(result, dict) else []
    rows = [row for frame in frames for row in _frame_rows(frame)]
    return {
        "http_status": status,
        "elapsed_ms": elapsed_ms,
        "error": result.get("error") if isinstance(result, dict) else payload,
        "rows": rows,
        "fields": sorted({key for row in rows for key in row}),
    }


def _workflow_identifier(rows: list[dict[str, Any]], expected_file: str) -> str | None:
    for row in rows:
        text_values = {str(value) for value in row.values() if value is not None}
        if not any(expected_file in value for value in text_values):
            continue
        for key in ("id", "ID", "workflowID", "workflowId", "databaseId"):
            value = row.get(key)
            if value is not None:
                return str(value)
    return None


def _query_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_count": len(result["rows"]),
        "elapsed_ms": result["elapsed_ms"],
        "fields": result["fields"],
        "error": result["error"],
    }


def validate(args: argparse.Namespace) -> None:
    base_url = args.base_url.rstrip("/")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    status, health = _request(
        f"{base_url}/api/datasources/uid/{DATASOURCE_UID}/health",
        timeout=60,
    )
    repositories_first = _query(
        base_url,
        {"queryType": "Repositories", "owner": args.owner, "repository": "", "options": {}},
    )
    repositories_repeat = _query(
        base_url,
        {"queryType": "Repositories", "owner": args.owner, "repository": "", "options": {}},
    )
    workflows = _query(
        base_url,
        {
            "queryType": "Workflows",
            "owner": args.owner,
            "repository": args.workflow_repository,
            "options": {"timeField": 0, "query": ""},
        },
    )
    workflow_id = _workflow_identifier(workflows["rows"], args.workflow_file)
    if workflow_id is None:
        workflow_runs = {
            "http_status": None,
            "elapsed_ms": 0.0,
            "error": "workflow identifier not found in Workflows response",
            "rows": [],
            "fields": [],
        }
    else:
        workflow_runs = _query(
            base_url,
            {
                "queryType": "Workflow_Runs",
                "owner": args.owner,
                "repository": args.workflow_repository,
                "options": {"workflowID": workflow_id, "branch": ""},
            },
        )
    pull_requests = _query(
        base_url,
        {
            "queryType": "Pull_Requests",
            "owner": args.owner,
            "repository": "",
            "options": {"query": "is:open author:app/renovate", "timeField": 4},
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
                "timeField": 2,
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

    repository_names = {
        str(row.get("name"))
        for row in repositories_first["rows"]
        if row.get("name") is not None
    }
    selected_expected = set(args.selected_repository)
    visible_selected = selected_expected & repository_names
    installation_scope_exceeds_runtime_selection = len(repository_names) > len(
        selected_expected
    )

    summary = {
        "schema_version": 1,
        "grafana": {
            "health_http_status": status,
            "health_status": health.get("status") if isinstance(health, dict) else None,
            "health_message": health.get("message") if isinstance(health, dict) else None,
            "image": args.grafana_image,
            "github_plugin": args.plugin_version,
        },
        "github_app": {
            "owner_type": args.owner_type,
            "runtime_selected_repositories": sorted(selected_expected),
            "runtime_selected_repositories_visible": sorted(visible_selected),
            "runtime_selected_repositories_all_visible": selected_expected <= repository_names,
            "installation_repositories_visible_count": len(repository_names),
            "installation_scope_exceeds_runtime_selection": installation_scope_exceeds_runtime_selection,
            "scope_interpretation": (
                "The plugin mints its own installation token from app id, installation id and private key; "
                "the token minted by the workflow does not downscope plugin queries."
            ),
        },
        "queries": {
            "repositories_first": _query_summary(repositories_first),
            "repositories_repeat": _query_summary(repositories_repeat),
            "workflows": _query_summary(workflows),
            "workflow_runs": {
                **_query_summary(workflow_runs),
                "workflow_identifier": workflow_id,
            },
            "pull_requests": _query_summary(pull_requests),
            "configuration_warning_issues": _query_summary(issues),
            "releases": _query_summary(releases),
        },
    }
    summary["assertions"] = {
        "datasource_healthy": summary["grafana"]["health_status"] == "OK",
        "selected_repositories_visible": selected_expected <= repository_names,
        "repositories_query_succeeded": repositories_first["error"] is None
        and bool(repositories_first["rows"]),
        "workflows_query_succeeded": workflows["error"] is None,
        "pull_requests_query_succeeded": pull_requests["error"] is None,
        "issues_query_succeeded": issues["error"] is None,
        "releases_query_succeeded": releases["error"] is None,
        "installation_scope_observed": installation_scope_exceeds_runtime_selection,
    }
    _write_json(output_dir / "summary.json", summary)

    failed = [name for name, passed in summary["assertions"].items() if not passed]
    if failed:
        raise SystemExit("failed assertions: " + ", ".join(failed))


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--provisioning-dir", required=True)
    prepare_parser.set_defaults(func=prepare)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--base-url", default="http://127.0.0.1:3000")
    validate_parser.add_argument("--output-dir", required=True)
    validate_parser.add_argument("--owner", required=True)
    validate_parser.add_argument(
        "--owner-type", choices=("User", "Organization"), required=True
    )
    validate_parser.add_argument("--workflow-repository", required=True)
    validate_parser.add_argument("--workflow-file", required=True)
    validate_parser.add_argument("--selected-repository", action="append", required=True)
    validate_parser.add_argument("--grafana-image", required=True)
    validate_parser.add_argument("--plugin-version", required=True)
    validate_parser.set_defaults(func=validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
