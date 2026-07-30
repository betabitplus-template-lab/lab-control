#!/usr/bin/env python3
"""Validate Ternforge Fleet Health end to end in Grafana Cloud.

The script intentionally uses only standard-library HTTP clients. Secrets are read from
runtime environment variables and never written to evidence. All Grafana resources
created by the experiment are deleted in a finally block.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

GITHUB_DATASOURCE_UID = "ternforge-github-lab"
PROMETHEUS_DATASOURCE_UID = "grafanacloud-prom"
FOLDER_UID = "ternforge-lab"
DASHBOARD_UID = "ternforge-fleet-health-lab"
CONTACT_POINT_UID = "ternforge-lab-webhook"
CONTACT_POINT_NAME = "Ternforge Lab Webhook"
ALERT_UID = "ternforge-cloud-update-processing-slow"
ALERT_LABELS = {"lab": "ternforge-fleet-health", "component": "update-delivery"}
METRIC_NAMES = {
    "ternforge_update_processing_duration_seconds",
    "ternforge_update_queue_delay_seconds",
    "ternforge_update_run_success",
    "ternforge_update_last_success_unixtime",
    "ternforge_fleet_expected_repositories",
    "ternforge_fleet_observed_repositories",
    "ternforge_fleet_token_scope_ok",
}


def _request(
    url: str,
    *,
    method: str = "GET",
    body: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 60,
) -> tuple[int, Any]:
    data: bytes | None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if body is None:
        data = None
    elif isinstance(body, bytes):
        data = body
    else:
        data = json.dumps(body).encode()
        request_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(
        url, data=data, method=method, headers=request_headers
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type", "")
            if not raw:
                payload: Any = None
            elif "json" in content_type:
                payload = json.loads(raw)
            else:
                try:
                    payload = json.loads(raw)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    payload = raw
            return response.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            payload = json.loads(raw) if raw else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = raw.decode(errors="replace")
        return exc.code, payload


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _grafana_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _grafana_request(
    base_url: str,
    token: str,
    path: str,
    *,
    method: str = "GET",
    body: Any | None = None,
    timeout: float = 60,
) -> tuple[int, Any]:
    return _request(
        base_url.rstrip("/") + path,
        method=method,
        body=body,
        headers=_grafana_headers(token),
        timeout=timeout,
    )


def _parse_otel_environment(text: str) -> tuple[str, str]:
    endpoint_match = re.search(
        r'OTEL_EXPORTER_OTLP_ENDPOINT="([^"]+)"', text
    )
    headers_match = re.search(
        r'OTEL_EXPORTER_OTLP_HEADERS="([^"]+)"', text
    )
    if not endpoint_match or not headers_match:
        raise ValueError("Grafana OTLP environment block is incomplete")
    endpoint = endpoint_match.group(1).rstrip("/")
    decoded = urllib.parse.unquote(headers_match.group(1))
    prefix = "Authorization="
    if not decoded.startswith(prefix):
        raise ValueError("Grafana OTLP authorization header is missing")
    authorization = decoded[len(prefix) :]
    if not authorization.startswith("Basic "):
        raise ValueError("Grafana OTLP authorization is not Basic auth")
    return endpoint, authorization


def prepare_collector(args: argparse.Namespace) -> None:
    endpoint, authorization = _parse_otel_environment(
        os.environ["GRAFANA_CLOUD_OTEL_ENV"]
    )
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Runtime-only file. It is never uploaded and is removed by the workflow.
    path.write_text(
        "receivers:\n"
        "  otlp:\n"
        "    protocols:\n"
        "      http:\n"
        "        endpoint: 0.0.0.0:4318\n\n"
        "extensions:\n"
        "  health_check:\n"
        "    endpoint: 0.0.0.0:13133\n\n"
        "exporters:\n"
        "  otlphttp/grafana:\n"
        f"    endpoint: {json.dumps(endpoint)}\n"
        "    headers:\n"
        f"      Authorization: {json.dumps(authorization)}\n"
        "    retry_on_failure:\n"
        "      enabled: true\n"
        "      initial_interval: 1s\n"
        "      max_interval: 5s\n"
        "      max_elapsed_time: 60s\n\n"
        "processors:\n"
        "  transform/fleet_health_labels:\n"
        "    error_mode: propagate\n"
        "    metric_statements:\n"
        "      - context: datapoint\n"
        "        statements:\n"
        "          - set(attributes[\"ternforge.trigger\"], resource.attributes[\"ternforge.trigger\"])\n\n"
        "service:\n"
        "  extensions: [health_check]\n"
        "  telemetry:\n"
        "    logs:\n"
        "      level: info\n"
        "  pipelines:\n"
        "    metrics:\n"
        "      receivers: [otlp]\n"
        "      processors: [transform/fleet_health_labels]\n"
        "      exporters: [otlphttp/grafana]\n"
    )
    # The container runs under a different UID. The file exists only on the
    # ephemeral runner and is mounted read-only, so it must be world-readable.
    os.chmod(path, 0o644)


def _metric(name: str, value: float, timestamp_ns: str) -> dict[str, Any]:
    return {
        "name": name,
        "gauge": {
            "dataPoints": [
                {"timeUnixNano": timestamp_ns, "asDouble": value}
            ]
        },
    }


def _resource_metrics(
    trigger: str, values: dict[str, float], timestamp_ns: str
) -> dict[str, Any]:
    return {
        "resource": {
            "attributes": [
                {
                    "key": "service.name",
                    "value": {"stringValue": "ternforge-update"},
                },
                {
                    "key": "deployment.environment",
                    "value": {"stringValue": "lab"},
                },
                {
                    "key": "ternforge.trigger",
                    "value": {"stringValue": trigger},
                },
            ]
        },
        "scopeMetrics": [
            {
                "scope": {"name": "ternforge.fleet-health", "version": "1"},
                "metrics": [
                    _metric(name, value, timestamp_ns)
                    for name, value in values.items()
                ],
            }
        ],
    }


def _metrics_payload(mode: str) -> dict[str, Any]:
    now = time.time()
    timestamp_ns = str(time.time_ns())
    if mode == "unhealthy":
        release = {
            "ternforge_update_processing_duration_seconds": 720,
            "ternforge_update_queue_delay_seconds": 31,
            "ternforge_update_run_success": 0,
            "ternforge_fleet_expected_repositories": 47,
            "ternforge_fleet_observed_repositories": 46,
            "ternforge_fleet_token_scope_ok": 0,
            "ternforge_update_last_success_unixtime": now - 200_000,
        }
    elif mode == "healthy":
        release = {
            "ternforge_update_processing_duration_seconds": 180,
            "ternforge_update_queue_delay_seconds": 4,
            "ternforge_update_run_success": 1,
            "ternforge_fleet_expected_repositories": 47,
            "ternforge_fleet_observed_repositories": 47,
            "ternforge_fleet_token_scope_ok": 1,
            "ternforge_update_last_success_unixtime": now,
        }
    else:
        raise ValueError(f"unsupported state: {mode}")
    auxiliary = {
        "ternforge_update_processing_duration_seconds": 60,
        "ternforge_update_queue_delay_seconds": 2,
        "ternforge_update_run_success": 1,
    }
    return {
        "resourceMetrics": [
            _resource_metrics("release", release, timestamp_ns),
            _resource_metrics("nightly", auxiliary, timestamp_ns),
            _resource_metrics("manual", auxiliary, timestamp_ns),
        ]
    }


def _emit_metrics(local_endpoint: str, mode: str) -> None:
    status, payload = _request(
        local_endpoint.rstrip("/") + "/v1/metrics",
        method="POST",
        body=_metrics_payload(mode),
        timeout=30,
    )
    if status not in {200, 202}:
        raise RuntimeError(f"local OTLP receiver rejected metrics: {status} {payload}")


def _frame_rows(frame: dict[str, Any]) -> list[dict[str, Any]]:
    fields = [field.get("name") for field in frame.get("schema", {}).get("fields", [])]
    values = frame.get("data", {}).get("values", [])
    if not fields or len(fields) != len(values):
        return []
    count = max((len(column) for column in values), default=0)
    rows: list[dict[str, Any]] = []
    for index in range(count):
        row: dict[str, Any] = {}
        for name, column in zip(fields, values, strict=True):
            if name is not None:
                row[name] = column[index] if index < len(column) else None
        rows.append(row)
    return rows


def _github_query(
    base_url: str, token: str, model: dict[str, Any]
) -> dict[str, Any]:
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
                    "uid": GITHUB_DATASOURCE_UID,
                },
                "intervalMs": 1_000,
                "maxDataPoints": 43_200,
            }
        ],
    }
    started = time.monotonic()
    status, payload = _grafana_request(
        base_url, token, "/api/ds/query", method="POST", body=body
    )
    elapsed_ms = round((time.monotonic() - started) * 1000, 1)
    result = (
        payload.get("results", {}).get("A", {})
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


def _query_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "http_status": result["http_status"],
        "row_count": len(result["rows"]),
        "elapsed_ms": result["elapsed_ms"],
        "fields": result["fields"],
        "error": result["error"],
    }


def _prometheus_path(path: str, params: dict[str, Any]) -> str:
    query = urllib.parse.urlencode(params, doseq=True)
    return (
        f"/api/datasources/proxy/uid/{PROMETHEUS_DATASOURCE_UID}"
        f"{path}?{query}"
    )


def _prom_query(base_url: str, token: str, expression: str) -> list[dict[str, Any]]:
    status, payload = _grafana_request(
        base_url,
        token,
        _prometheus_path("/api/v1/query", {"query": expression}),
    )
    if (
        status != 200
        or not isinstance(payload, dict)
        or payload.get("status") != "success"
    ):
        raise RuntimeError(f"Grafana Cloud Prometheus query failed: {status} {payload}")
    return payload.get("data", {}).get("result", [])


def _prom_scalar(base_url: str, token: str, expression: str) -> float | None:
    result = _prom_query(base_url, token, expression)
    if not result:
        return None
    value = result[0].get("value")
    if not isinstance(value, list) or len(value) != 2:
        return None
    return float(value[1])


def _wait_scalar(
    base_url: str,
    token: str,
    expression: str,
    expected: float,
    *,
    timeout_seconds: int = 240,
) -> float:
    deadline = time.monotonic() + timeout_seconds
    last: float | None = None
    while time.monotonic() < deadline:
        last = _prom_scalar(base_url, token, expression)
        if last is not None and abs(last - expected) < 0.001:
            return last
        time.sleep(5)
    raise RuntimeError(
        f"Cloud metric did not converge: {expression!r}; last={last!r}"
    )


def _prom_series(base_url: str, token: str) -> list[dict[str, str]]:
    status, payload = _grafana_request(
        base_url,
        token,
        _prometheus_path(
            "/api/v1/series", {"match[]": '{__name__=~"ternforge_.*"}'}
        ),
    )
    if (
        status != 200
        or not isinstance(payload, dict)
        or payload.get("status") != "success"
    ):
        raise RuntimeError(f"Cloud series query failed: {status} {payload}")
    return payload.get("data", [])


def _github_api_scope(token: str) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    status, repositories = _request(
        "https://api.github.com/installation/repositories?per_page=100",
        headers=headers,
    )
    selected_status, _ = _request(
        "https://api.github.com/repos/betabitplus-template-lab/lab-control",
        headers=headers,
    )
    unselected_status, unselected_payload = _request(
        "https://api.github.com/repos/betabitplus-template-lab/"
        "sandbox-private-uv-source-20260724-r1",
        headers=headers,
    )
    workflow_runs_status, workflow_runs_payload = _request(
        "https://api.github.com/repos/betabitplus-template-lab/lab-control/"
        "actions/workflows/grafana-cloud-fleet-health-lab.yml/runs?per_page=5",
        headers=headers,
    )
    names = (
        [item.get("full_name") for item in repositories.get("repositories", [])]
        if isinstance(repositories, dict)
        else []
    )
    return {
        "repositories_http_status": status,
        "repository_count": repositories.get("total_count")
        if isinstance(repositories, dict)
        else None,
        "repositories": names,
        "selected_repository_http_status": selected_status,
        "unselected_private_repository_http_status": unselected_status,
        "workflow_runs_http_status": workflow_runs_status,
        "workflow_runs_count": workflow_runs_payload.get("total_count")
        if isinstance(workflow_runs_payload, dict)
        else None,
        "unselected_private_message": unselected_payload.get("message")
        if isinstance(unselected_payload, dict)
        else None,
    }


def _create_folder(base_url: str, token: str) -> dict[str, Any]:
    _grafana_request(base_url, token, f"/api/folders/{FOLDER_UID}", method="DELETE")
    status, payload = _grafana_request(
        base_url,
        token,
        "/api/folders",
        method="POST",
        body={"uid": FOLDER_UID, "title": "Ternforge Lab"},
    )
    if status not in {200, 201}:
        raise RuntimeError(f"folder creation failed: {status} {payload}")
    return {"http_status": status, "uid": payload.get("uid")}


def _create_github_datasource(base_url: str, token: str) -> dict[str, Any]:
    _grafana_request(
        base_url,
        token,
        f"/api/datasources/uid/{GITHUB_DATASOURCE_UID}",
        method="DELETE",
    )
    payload = {
        "name": "Ternforge GitHub Lab",
        "type": "grafana-github-datasource",
        "uid": GITHUB_DATASOURCE_UID,
        "access": "proxy",
        "isDefault": False,
        "editable": False,
        "jsonData": {
            "selectedAuthType": "github-app",
            "appId": os.environ["FLEET_HEALTH_GITHUB_APP_ID"],
            "installationId": os.environ[
                "FLEET_HEALTH_GITHUB_APP_INSTALLATION_ID"
            ],
            "cachingEnabled": True,
        },
        "secureJsonData": {
            "privateKey": os.environ["FLEET_HEALTH_GITHUB_APP_PRIVATE_KEY"]
        },
    }
    status, response = _grafana_request(
        base_url, token, "/api/datasources", method="POST", body=payload
    )
    if status not in {200, 201}:
        raise RuntimeError(f"GitHub datasource creation failed: {status} {response}")
    health_status, health = _grafana_request(
        base_url,
        token,
        f"/api/datasources/uid/{GITHUB_DATASOURCE_UID}/health",
        timeout=120,
    )
    if health_status != 200 or not isinstance(health, dict) or health.get("status") != "OK":
        raise RuntimeError(f"GitHub datasource unhealthy: {health_status} {health}")
    return {
        "create_http_status": status,
        "health_http_status": health_status,
        "health_status": health.get("status"),
        "health_message": health.get("message"),
    }


def _dashboard() -> dict[str, Any]:
    metric_ds = {"type": "prometheus", "uid": PROMETHEUS_DATASOURCE_UID}
    github_ds = {
        "type": "grafana-github-datasource",
        "uid": GITHUB_DATASOURCE_UID,
    }
    return {
        "uid": DASHBOARD_UID,
        "title": "Ternforge Fleet Health Lab",
        "tags": ["ternforge", "lab", "fleet-health"],
        "timezone": "browser",
        "schemaVersion": 41,
        "version": 0,
        "refresh": "30s",
        "time": {"from": "now-24h", "to": "now"},
        "panels": [
            {
                "id": 1,
                "type": "stat",
                "title": "Processing duration",
                "datasource": metric_ds,
                "gridPos": {"h": 6, "w": 6, "x": 0, "y": 0},
                "targets": [
                    {
                        "refId": "A",
                        "expr": 'ternforge_update_processing_duration_seconds{ternforge_trigger="release"}',
                        "instant": True,
                    }
                ],
                "fieldConfig": {"defaults": {"unit": "s"}, "overrides": []},
            },
            {
                "id": 2,
                "type": "stat",
                "title": "Last run success",
                "datasource": metric_ds,
                "gridPos": {"h": 6, "w": 6, "x": 6, "y": 0},
                "targets": [
                    {
                        "refId": "A",
                        "expr": 'ternforge_update_run_success{ternforge_trigger="release"}',
                        "instant": True,
                    }
                ],
            },
            {
                "id": 3,
                "type": "stat",
                "title": "Fleet coverage gap",
                "datasource": metric_ds,
                "gridPos": {"h": 6, "w": 6, "x": 12, "y": 0},
                "targets": [
                    {
                        "refId": "A",
                        "expr": 'abs(ternforge_fleet_expected_repositories{ternforge_trigger="release"} - ternforge_fleet_observed_repositories{ternforge_trigger="release"})',
                        "instant": True,
                    }
                ],
            },
            {
                "id": 4,
                "type": "stat",
                "title": "Token scope valid",
                "datasource": metric_ds,
                "gridPos": {"h": 6, "w": 6, "x": 18, "y": 0},
                "targets": [
                    {
                        "refId": "A",
                        "expr": 'ternforge_fleet_token_scope_ok{ternforge_trigger="release"}',
                        "instant": True,
                    }
                ],
            },
            {
                "id": 5,
                "type": "timeseries",
                "title": "Processing and queue delay",
                "datasource": metric_ds,
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 6},
                "targets": [
                    {
                        "refId": "A",
                        "expr": 'ternforge_update_processing_duration_seconds{ternforge_trigger="release"}',
                    },
                    {
                        "refId": "B",
                        "expr": 'ternforge_update_queue_delay_seconds{ternforge_trigger="release"}',
                    },
                ],
                "fieldConfig": {"defaults": {"unit": "s"}, "overrides": []},
            },
            {
                "id": 6,
                "type": "table",
                "title": "Managed repositories",
                "datasource": github_ds,
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 6},
                "targets": [
                    {
                        "refId": "A",
                        "queryType": "Repositories",
                        "owner": "betabitplus-template-lab",
                        "repository": "lab-control in:name",
                        "options": {},
                    }
                ],
            },
            {
                "id": 7,
                "type": "table",
                "title": "Open Renovate pull requests",
                "datasource": github_ds,
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 14},
                "targets": [
                    {
                        "refId": "A",
                        "queryType": "Pull_Requests",
                        "owner": "betabitplus-template-lab",
                        "repository": "",
                        "options": {
                            "query": "is:open author:app/renovate",
                            "timeField": 4,
                        },
                    }
                ],
            },
        ],
    }


def _create_dashboard(base_url: str, token: str) -> dict[str, Any]:
    _grafana_request(
        base_url, token, f"/api/dashboards/uid/{DASHBOARD_UID}", method="DELETE"
    )
    status, payload = _grafana_request(
        base_url,
        token,
        "/api/dashboards/db",
        method="POST",
        body={
            "dashboard": _dashboard(),
            "folderUid": FOLDER_UID,
            "overwrite": True,
            "message": "Ternforge Fleet Health lab experiment",
        },
    )
    if status not in {200, 201}:
        raise RuntimeError(f"dashboard creation failed: {status} {payload}")
    get_status, dashboard = _grafana_request(
        base_url, token, f"/api/dashboards/uid/{DASHBOARD_UID}"
    )
    panels = (
        dashboard.get("dashboard", {}).get("panels", [])
        if isinstance(dashboard, dict)
        else []
    )
    return {
        "create_http_status": status,
        "get_http_status": get_status,
        "uid": payload.get("uid") if isinstance(payload, dict) else None,
        "url": payload.get("url") if isinstance(payload, dict) else None,
        "panel_count": len(panels),
        "panel_titles": [panel.get("title") for panel in panels],
    }


def _create_contact_point(base_url: str, token: str, webhook_url: str) -> dict[str, Any]:
    _grafana_request(
        base_url,
        token,
        f"/api/v1/provisioning/contact-points/{CONTACT_POINT_UID}",
        method="DELETE",
    )
    status, payload = _grafana_request(
        base_url,
        token,
        "/api/v1/provisioning/contact-points",
        method="POST",
        body={
            "uid": CONTACT_POINT_UID,
            "name": CONTACT_POINT_NAME,
            "type": "webhook",
            "settings": {"url": webhook_url, "httpMethod": "POST"},
            "disableResolveMessage": False,
        },
    )
    if status not in {200, 201, 202}:
        raise RuntimeError(f"contact point creation failed: {status} {payload}")
    return {"http_status": status, "uid": payload.get("uid") if isinstance(payload, dict) else None}


def _alert_rule() -> dict[str, Any]:
    return {
        "uid": ALERT_UID,
        "title": "Ternforge update processing exceeds ten minutes",
        "ruleGroup": "ternforge-cloud-fleet-health",
        "folderUID": FOLDER_UID,
        "orgId": 1,
        "condition": "B",
        "data": [
            {
                "refId": "A",
                "relativeTimeRange": {"from": 600, "to": 0},
                "datasourceUid": PROMETHEUS_DATASOURCE_UID,
                "model": {
                    "datasource": {
                        "type": "prometheus",
                        "uid": PROMETHEUS_DATASOURCE_UID,
                    },
                    "editorMode": "code",
                    "expr": 'ternforge_update_processing_duration_seconds{ternforge_trigger="release"}',
                    "instant": True,
                    "intervalMs": 1000,
                    "maxDataPoints": 43200,
                    "range": False,
                    "refId": "A",
                },
            },
            {
                "refId": "B",
                "relativeTimeRange": {"from": 0, "to": 0},
                "datasourceUid": "__expr__",
                "model": {
                    "datasource": {"type": "__expr__", "uid": "__expr__"},
                    "expression": "A",
                    "conditions": [
                        {
                            "evaluator": {"params": [600], "type": "gt"},
                            "operator": {"type": "and"},
                            "query": {"params": ["B"]},
                            "reducer": {"params": [], "type": "last"},
                            "type": "query",
                        }
                    ],
                    "intervalMs": 1000,
                    "maxDataPoints": 43200,
                    "refId": "B",
                    "type": "threshold",
                },
            },
        ],
        "noDataState": "NoData",
        "execErrState": "Error",
        "for": "0s",
        "annotations": {
            "summary": "A completed full-fleet update took longer than ten minutes."
        },
        "labels": ALERT_LABELS,
        "isPaused": False,
        "notification_settings": {"receiver": CONTACT_POINT_NAME},
    }


def _create_alert_rule(base_url: str, token: str) -> dict[str, Any]:
    _grafana_request(
        base_url,
        token,
        f"/api/v1/provisioning/alert-rules/{ALERT_UID}",
        method="DELETE",
    )
    status, payload = _grafana_request(
        base_url,
        token,
        "/api/v1/provisioning/alert-rules",
        method="POST",
        body=_alert_rule(),
        timeout=120,
    )
    if status not in {200, 201, 202}:
        raise RuntimeError(f"alert rule creation failed: {status} {payload}")
    return {"http_status": status, "uid": payload.get("uid") if isinstance(payload, dict) else None}


def _active_alert_uids(base_url: str, token: str) -> set[str]:
    status, payload = _grafana_request(
        base_url, token, "/api/alertmanager/grafana/api/v2/alerts"
    )
    if status != 200 or not isinstance(payload, list):
        return set()
    active: set[str] = set()
    for alert in payload:
        if not isinstance(alert, dict):
            continue
        labels = alert.get("labels", {})
        state = alert.get("status", {}).get("state")
        if state == "active" and isinstance(labels, dict):
            uid = labels.get("__alert_rule_uid__")
            if isinstance(uid, str):
                active.add(uid)
    return active


def _wait_alert(
    base_url: str,
    token: str,
    *,
    expected_active: bool,
    timeout_seconds: int = 240,
) -> set[str]:
    deadline = time.monotonic() + timeout_seconds
    observed: set[str] = set()
    while time.monotonic() < deadline:
        observed = _active_alert_uids(base_url, token)
        if (ALERT_UID in observed) == expected_active:
            return observed
        time.sleep(10)
    raise RuntimeError(
        f"alert state did not converge; expected_active={expected_active}, observed={sorted(observed)}"
    )


def _webhook_requests(uuid: str) -> dict[str, Any]:
    status, payload = _request(
        f"https://webhook.site/token/{uuid}/requests?sorting=newest"
    )
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"webhook.site query failed: {status} {payload}")
    return payload


def _wait_webhook(uuid: str, baseline: int, timeout_seconds: int = 240) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        last = _webhook_requests(uuid)
        total = int(last.get("total") or 0)
        if total > baseline:
            item = (last.get("data") or [{}])[0]
            content = item.get("content", "") if isinstance(item, dict) else ""
            return {
                "total": total,
                "method": item.get("method") if isinstance(item, dict) else None,
                "content_type": item.get("content_type") if isinstance(item, dict) else None,
                "content_mentions_rule": ALERT_UID in str(content)
                or "exceeds ten minutes" in str(content),
                "created_at": item.get("created_at") if isinstance(item, dict) else None,
            }
        time.sleep(10)
    raise RuntimeError(f"no Grafana webhook received; last total={last.get('total')}")


def _render_dashboard(
    base_url: str, token: str, output_dir: Path
) -> dict[str, Any]:
    path = (
        f"/render/d/{DASHBOARD_UID}/ternforge-fleet-health-lab"
        "?from=now-24h&to=now&width=1600&height=1000&tz=UTC"
    )
    status, payload = _grafana_request(
        base_url, token, path, timeout=180
    )
    if status == 200 and isinstance(payload, bytes) and payload.startswith(b"\x89PNG"):
        image_path = output_dir / "fleet-health-dashboard.png"
        image_path.write_bytes(payload)
        return {"http_status": status, "png_created": True, "bytes": len(payload)}
    return {
        "http_status": status,
        "png_created": False,
        "response_type": type(payload).__name__,
    }


def _cleanup(base_url: str, token: str) -> dict[str, int]:
    endpoints = [
        (f"/api/v1/provisioning/alert-rules/{ALERT_UID}", "DELETE"),
        (f"/api/v1/provisioning/contact-points/{CONTACT_POINT_UID}", "DELETE"),
        (f"/api/dashboards/uid/{DASHBOARD_UID}", "DELETE"),
        (f"/api/datasources/uid/{GITHUB_DATASOURCE_UID}", "DELETE"),
        (f"/api/folders/{FOLDER_UID}", "DELETE"),
    ]
    result: dict[str, int] = {}
    for path, method in endpoints:
        status, _ = _grafana_request(base_url, token, path, method=method)
        result[path] = status
    return result


def validate(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = args.grafana_url.rstrip("/")
    grafana_token = os.environ["GRAFANA_CLOUD_SERVICE_ACCOUNT_TOKEN"].strip()
    webhook_url = os.environ["GRAFANA_CLOUD_WEBHOOK_URL"].strip()
    webhook_uuid = webhook_url.rstrip("/").rsplit("/", 1)[-1]
    scoped_app_token = os.environ["SCOPED_APP_TOKEN"].strip()

    summary: dict[str, Any] = {
        "schema_version": 1,
        "environment": {
            "grafana_stack": base_url,
            "github_owner": "betabitplus-template-lab",
            "selected_repository": "lab-control",
        },
        "assertions": {},
    }
    failure: str | None = None
    try:
        health_status, health = _grafana_request(base_url, grafana_token, "/api/health")
        plugin_status, plugin = _grafana_request(
            base_url,
            grafana_token,
            "/api/plugins/grafana-github-datasource/settings",
        )
        summary["grafana"] = {
            "health_http_status": health_status,
            "database": health.get("database") if isinstance(health, dict) else None,
            "version": health.get("version") if isinstance(health, dict) else None,
            "plugin_http_status": plugin_status,
            "plugin_version": plugin.get("info", {}).get("version")
            if isinstance(plugin, dict)
            else None,
            "plugin_enabled": plugin.get("enabled") if isinstance(plugin, dict) else None,
        }

        app_scope = _github_api_scope(scoped_app_token)
        summary["github_app_scope"] = app_scope

        summary["resources"] = {
            "folder": _create_folder(base_url, grafana_token),
            "github_datasource": _create_github_datasource(base_url, grafana_token),
        }

        repositories = _github_query(
            base_url,
            grafana_token,
            {
                "queryType": "Repositories",
                "owner": "betabitplus-template-lab",
                "repository": "",
                "options": {},
            },
        )
        managed_repositories = _github_query(
            base_url,
            grafana_token,
            {
                "queryType": "Repositories",
                "owner": "betabitplus-template-lab",
                "repository": "lab-control in:name",
                "options": {},
            },
        )
        workflows = _github_query(
            base_url,
            grafana_token,
            {
                "queryType": "Workflows",
                "owner": "betabitplus-template-lab",
                "repository": "lab-control",
                "options": {"timeField": 0, "query": ""},
            },
        )
        workflow_candidates: list[str] = [
            args.workflow_file,
            f".github/workflows/{args.workflow_file}",
        ]
        for row in workflows["rows"]:
            path_value = row.get("path")
            name_value = row.get("name")
            id_value = row.get("id")
            if path_value and args.workflow_file in str(path_value):
                for value in (str(id_value) if id_value is not None else None, str(path_value), str(name_value) if name_value else None):
                    if value and value not in workflow_candidates:
                        workflow_candidates.append(value)
        workflow_run_attempts: list[dict[str, Any]] = []
        workflow_runs: dict[str, Any] | None = None
        selected_workflow_identifier: str | None = None
        for candidate in workflow_candidates:
            attempt = _github_query(
                base_url,
                grafana_token,
                {
                    "queryType": "Workflow_Runs",
                    "owner": "betabitplus-template-lab",
                    "repository": "lab-control",
                    # Plugin 2.8.0 frontend calls this workflowID, but its Go
                    # backend only deserializes options.workflow.
                    "options": {"workflow": candidate, "branch": ""},
                },
            )
            workflow_run_attempts.append(
                {
                    "identifier": candidate,
                    "http_status": attempt["http_status"],
                    "row_count": len(attempt["rows"]),
                    "error": attempt["error"],
                }
            )
            if attempt["error"] is None and attempt["rows"]:
                workflow_runs = attempt
                selected_workflow_identifier = candidate
                break
        if workflow_runs is None:
            workflow_runs = workflow_run_attempts and _github_query(
                base_url,
                grafana_token,
                {
                    "queryType": "Workflow_Runs",
                    "owner": "betabitplus-template-lab",
                    "repository": "lab-control",
                    "options": {"workflow": workflow_candidates[0], "branch": ""},
                },
            )

        pull_requests = _github_query(
            base_url,
            grafana_token,
            {
                "queryType": "Pull_Requests",
                "owner": "betabitplus-template-lab",
                "repository": "",
                "options": {"query": "is:open author:app/renovate", "timeField": 4},
            },
        )
        issues = _github_query(
            base_url,
            grafana_token,
            {
                "queryType": "Issues",
                "owner": "betabitplus-template-lab",
                "repository": "",
                "options": {"query": "is:open label:renovate/config-error", "timeField": 2},
            },
        )
        releases = _github_query(
            base_url,
            grafana_token,
            {
                "queryType": "Releases",
                "owner": "betabitplus-template-lab",
                "repository": "lab-control",
                "options": {},
            },
        )
        unselected_private = _github_query(
            base_url,
            grafana_token,
            {
                "queryType": "Workflows",
                "owner": "betabitplus-template-lab",
                "repository": "sandbox-private-uv-source-20260724-r1",
                "options": {"timeField": 0, "query": ""},
            },
        )
        repository_names = sorted(
            {
                str(row.get("name"))
                for row in repositories["rows"]
                if row.get("name") is not None
            }
        )
        managed_repository_names = sorted(
            {
                str(row.get("name"))
                for row in managed_repositories["rows"]
                if row.get("name") is not None
            }
        )
        summary["github_datasource"] = {
            "repositories": _query_summary(repositories),
            "repository_names": repository_names,
            "public_owner_visibility_count": len(repository_names),
            "managed_repositories": _query_summary(managed_repositories),
            "managed_repository_names": managed_repository_names,
            "workflows": _query_summary(workflows),
            "workflow_runs": _query_summary(workflow_runs),
            "workflow_identifier": selected_workflow_identifier,
            "workflow_run_attempts": workflow_run_attempts,
            "pull_requests": _query_summary(pull_requests),
            "configuration_warning_issues": _query_summary(issues),
            "releases": _query_summary(releases),
            "unselected_private_repository": _query_summary(unselected_private),
        }

        webhook_baseline = int(_webhook_requests(webhook_uuid).get("total") or 0)
        _emit_metrics(args.local_otlp_endpoint, "unhealthy")
        unhealthy_values = {
            "duration": _wait_scalar(
                base_url,
                grafana_token,
                'ternforge_update_processing_duration_seconds{ternforge_trigger="release"}',
                720,
            ),
            "success": _wait_scalar(
                base_url,
                grafana_token,
                'ternforge_update_run_success{ternforge_trigger="release"}',
                0,
            ),
            "coverage_gap": _wait_scalar(
                base_url,
                grafana_token,
                'abs(ternforge_fleet_expected_repositories{ternforge_trigger="release"} - ternforge_fleet_observed_repositories{ternforge_trigger="release"})',
                1,
            ),
            "token_scope_ok": _wait_scalar(
                base_url,
                grafana_token,
                'ternforge_fleet_token_scope_ok{ternforge_trigger="release"}',
                0,
            ),
        }
        stale_seconds = _prom_scalar(
            base_url,
            grafana_token,
            'time() - ternforge_update_last_success_unixtime{ternforge_trigger="release"}',
        )
        series = _prom_series(base_url, grafana_token)
        metric_names = sorted({item.get("__name__", "") for item in series})
        triggers = sorted(
            {
                item.get("ternforge_trigger", "")
                for item in series
                if item.get("ternforge_trigger")
            }
        )
        forbidden_labels = sorted(
            {
                key
                for item in series
                for key in item
                if key in {"repository", "run_id", "source_sha", "source_ref"}
            }
        )

        summary["resources"].update(
            {
                "dashboard": _create_dashboard(base_url, grafana_token),
                "contact_point": _create_contact_point(
                    base_url, grafana_token, webhook_url
                ),
                "alert_rule": _create_alert_rule(base_url, grafana_token),
            }
        )
        firing_alerts = _wait_alert(
            base_url, grafana_token, expected_active=True
        )
        webhook = _wait_webhook(webhook_uuid, webhook_baseline)
        dashboard_render = _render_dashboard(base_url, grafana_token, output_dir)

        _emit_metrics(args.local_otlp_endpoint, "healthy")
        healthy_values = {
            "duration": _wait_scalar(
                base_url,
                grafana_token,
                'ternforge_update_processing_duration_seconds{ternforge_trigger="release"}',
                180,
            ),
            "success": _wait_scalar(
                base_url,
                grafana_token,
                'ternforge_update_run_success{ternforge_trigger="release"}',
                1,
            ),
            "coverage_gap": _wait_scalar(
                base_url,
                grafana_token,
                'abs(ternforge_fleet_expected_repositories{ternforge_trigger="release"} - ternforge_fleet_observed_repositories{ternforge_trigger="release"})',
                0,
            ),
            "token_scope_ok": _wait_scalar(
                base_url,
                grafana_token,
                'ternforge_fleet_token_scope_ok{ternforge_trigger="release"}',
                1,
            ),
        }
        fresh_seconds = _prom_scalar(
            base_url,
            grafana_token,
            'time() - ternforge_update_last_success_unixtime{ternforge_trigger="release"}',
        )
        resolved_alerts = _wait_alert(
            base_url, grafana_token, expected_active=False
        )

        summary["metrics"] = {
            "metric_names": metric_names,
            "series_count": len(series),
            "trigger_values": triggers,
            "forbidden_high_cardinality_labels": forbidden_labels,
            "unhealthy": {
                "values": unhealthy_values,
                "freshness_seconds": stale_seconds,
            },
            "healthy": {
                "values": healthy_values,
                "freshness_seconds": fresh_seconds,
            },
        }
        summary["alerting"] = {
            "firing_alert_uids": sorted(firing_alerts),
            "resolved_alert_uids": sorted(resolved_alerts),
            "webhook": webhook,
        }
        summary["dashboard_render"] = dashboard_render

        assertions = {
            "grafana_cloud_healthy": health_status == 200
            and isinstance(health, dict)
            and health.get("database") == "ok",
            "github_plugin_installed": plugin_status == 200,
            "app_installation_exactly_one_repository": app_scope["repository_count"] == 1
            and app_scope["repositories"] == ["betabitplus-template-lab/lab-control"],
            "app_selected_repository_accessible": app_scope[
                "selected_repository_http_status"
            ]
            == 200,
            "app_unselected_private_repository_denied": app_scope[
                "unselected_private_repository_http_status"
            ]
            == 404,
            "github_datasource_healthy": summary["resources"]["github_datasource"][
                "health_status"
            ]
            == "OK",
            "app_workflow_runs_permission_works": app_scope["workflow_runs_http_status"]
            == 200
            and bool(app_scope["workflow_runs_count"]),
            "github_owner_query_includes_selected_repository": "lab-control"
            in repository_names,
            "github_managed_repository_query_exact": managed_repository_names
            == ["lab-control"],
            "github_workflows_query_succeeded": workflows["error"] is None
            and bool(workflows["rows"]),
            "github_workflow_runs_query_succeeded": workflow_runs["error"] is None
            and bool(workflow_runs["rows"]),
            "github_pull_requests_query_succeeded": pull_requests["error"] is None,
            "github_issues_query_succeeded": issues["error"] is None,
            "github_releases_query_succeeded": releases["error"] is None,
            "github_unselected_private_query_denied": unselected_private["error"]
            is not None
            or unselected_private["http_status"] in {401, 403, 404},
            "all_metrics_ingested": METRIC_NAMES <= set(metric_names),
            "metric_series_bounded": len(series) <= 20,
            "metric_trigger_cardinality_bounded": triggers
            == ["manual", "nightly", "release"],
            "no_high_cardinality_labels": not forbidden_labels,
            "unhealthy_metric_values_correct": unhealthy_values
            == {
                "duration": 720.0,
                "success": 0.0,
                "coverage_gap": 1.0,
                "token_scope_ok": 0.0,
            },
            "healthy_metric_values_correct": healthy_values
            == {
                "duration": 180.0,
                "success": 1.0,
                "coverage_gap": 0.0,
                "token_scope_ok": 1.0,
            },
            "stale_recovery_signal_correct": stale_seconds is not None
            and stale_seconds > 129_600,
            "fresh_recovery_signal_correct": fresh_seconds is not None
            and fresh_seconds < 120,
            "dashboard_created_with_expected_panels": summary["resources"]["dashboard"][
                "panel_count"
            ]
            == 7,
            "cloud_alert_fired": ALERT_UID in firing_alerts,
            "cloud_alert_resolved": ALERT_UID not in resolved_alerts,
            "webhook_notification_delivered": webhook["total"] > webhook_baseline
            and webhook["method"] == "POST",
        }
        summary["assertions"] = assertions
        failed = [name for name, passed in assertions.items() if not passed]
        if failed:
            raise RuntimeError("failed assertions: " + ", ".join(failed))
    except Exception as exc:  # noqa: BLE001 - evidence must retain the failure summary
        failure = f"{type(exc).__name__}: {exc}"
        summary["failure"] = failure
        raise
    finally:
        cleanup = _cleanup(base_url, grafana_token)
        summary["cleanup_http_status"] = cleanup
        _write_json(output_dir / "summary.json", summary)
        if failure:
            (output_dir / "failure.txt").write_text(failure + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-collector")
    prepare.add_argument("--output", required=True)
    prepare.set_defaults(func=prepare_collector)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--output-dir", required=True)
    validate_parser.add_argument(
        "--grafana-url", default="https://cleverhop2412.grafana.net"
    )
    validate_parser.add_argument(
        "--local-otlp-endpoint", default="http://127.0.0.1:4318"
    )
    validate_parser.add_argument(
        "--workflow-file", default="grafana-cloud-fleet-health-lab.yml"
    )
    validate_parser.set_defaults(func=validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
