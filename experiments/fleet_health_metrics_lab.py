#!/usr/bin/env python3
"""Exercise a bounded OTLP fleet-health metric contract and Grafana alerts."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ALERT_UIDS = {
    "update-run-failed",
    "update-processing-slow",
    "fleet-coverage-mismatch",
    "fleet-token-scope-mismatch",
    "update-recovery-stale",
}


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
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
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


def _metric(name: str, value: float, timestamp_ns: str) -> dict[str, Any]:
    return {
        "name": name,
        "gauge": {
            "dataPoints": [
                {
                    "timeUnixNano": timestamp_ns,
                    "asDouble": value,
                }
            ]
        },
    }


def _resource_metrics(
    trigger: str,
    values: dict[str, float],
    timestamp_ns: str,
) -> dict[str, Any]:
    return {
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": "ternforge-update"}},
                {"key": "ternforge.trigger", "value": {"stringValue": trigger}},
            ]
        },
        "scopeMetrics": [
            {
                "scope": {"name": "ternforge.fleet-health", "version": "1"},
                "metrics": [
                    _metric(name, value, timestamp_ns) for name, value in values.items()
                ],
            }
        ],
    }


def _payload(mode: str) -> dict[str, Any]:
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
        raise ValueError(f"unsupported mode: {mode}")

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


def emit(endpoint: str, mode: str) -> None:
    status, payload = _request(
        endpoint.rstrip("/") + "/v1/metrics",
        method="POST",
        body=_payload(mode),
    )
    if status not in {200, 202}:
        raise SystemExit(f"OTLP export failed: {status} {payload}")


def _prom_query(base_url: str, expression: str) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"query": expression})
    status, payload = _request(base_url.rstrip("/") + "/api/v1/query?" + query)
    if status != 200 or not isinstance(payload, dict) or payload.get("status") != "success":
        raise RuntimeError(f"Prometheus query failed: {status} {payload}")
    return payload.get("data", {}).get("result", [])


def _scalar(base_url: str, expression: str) -> float | None:
    result = _prom_query(base_url, expression)
    if not result:
        return None
    value = result[0].get("value")
    if not isinstance(value, list) or len(value) != 2:
        return None
    return float(value[1])


def _wait_scalar(
    base_url: str,
    expression: str,
    expected: float,
    *,
    timeout_seconds: int = 60,
) -> float:
    deadline = time.monotonic() + timeout_seconds
    current: float | None = None
    while time.monotonic() < deadline:
        current = _scalar(base_url, expression)
        if current is not None and abs(current - expected) < 0.001:
            return current
        time.sleep(2)
    raise RuntimeError(f"query did not converge: {expression!r}, last={current!r}")


def _alert_state(base_url: str) -> dict[str, Any]:
    observations: dict[str, Any] = {}
    for endpoint in (
        "/api/prometheus/grafana/api/v1/alerts",
        "/api/prometheus/grafana/api/v1/rules",
        "/api/alertmanager/grafana/api/v2/alerts",
    ):
        status, payload = _request(base_url.rstrip("/") + endpoint)
        observations[endpoint] = {"status": status, "payload": payload}
    return observations


def _matched_alert_uids(observations: dict[str, Any]) -> set[str]:
    alertmanager = observations.get("/api/alertmanager/grafana/api/v2/alerts", {})
    payload = alertmanager.get("payload") if isinstance(alertmanager, dict) else None
    if not isinstance(payload, list):
        return set()
    matched: set[str] = set()
    for alert in payload:
        if not isinstance(alert, dict):
            continue
        labels = alert.get("labels", {})
        status = alert.get("status", {})
        if not isinstance(labels, dict) or not isinstance(status, dict):
            continue
        if status.get("state") != "active" or labels.get("alertname") == "DatasourceNoData":
            continue
        uid = labels.get("__alert_rule_uid__")
        if isinstance(uid, str) and uid in ALERT_UIDS:
            matched.add(uid)
    return matched


def _wait_alerts(
    base_url: str,
    expected: set[str],
    *,
    timeout_seconds: int = 90,
) -> tuple[set[str], dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    matched: set[str] = set()
    observations: dict[str, Any] = {}
    while time.monotonic() < deadline:
        observations = _alert_state(base_url)
        matched = _matched_alert_uids(observations)
        if matched == expected:
            return matched, observations
        time.sleep(5)
    return matched, observations


def _series(base_url: str) -> list[dict[str, str]]:
    query = urllib.parse.urlencode(
        {"match[]": '{__name__=~"ternforge_.*"}'}, doseq=True
    )
    status, payload = _request(base_url.rstrip("/") + "/api/v1/series?" + query)
    if status != 200 or not isinstance(payload, dict) or payload.get("status") != "success":
        raise RuntimeError(f"series query failed: {status} {payload}")
    return payload.get("data", [])


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def validate(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    emit(args.otlp_endpoint, "unhealthy")
    unhealthy_values = {
        "duration": _wait_scalar(
            args.prometheus_url,
            'ternforge_update_processing_duration_seconds{ternforge_trigger="release"}',
            720,
        ),
        "success": _wait_scalar(
            args.prometheus_url,
            'ternforge_update_run_success{ternforge_trigger="release"}',
            0,
        ),
        "coverage_gap": _wait_scalar(
            args.prometheus_url,
            'abs(ternforge_fleet_expected_repositories{ternforge_trigger="release"} - ternforge_fleet_observed_repositories{ternforge_trigger="release"})',
            1,
        ),
        "token_scope_ok": _wait_scalar(
            args.prometheus_url,
            'ternforge_fleet_token_scope_ok{ternforge_trigger="release"}',
            0,
        ),
    }
    stale_seconds = _scalar(
        args.prometheus_url,
        'time() - ternforge_update_last_success_unixtime{ternforge_trigger="release"}',
    )
    unhealthy_alerts, unhealthy_alert_observation = _wait_alerts(
        args.grafana_url, ALERT_UIDS
    )

    series = _series(args.prometheus_url)
    triggers = sorted(
        {item.get("ternforge_trigger", "") for item in series if item.get("ternforge_trigger")}
    )
    forbidden_labels = sorted(
        {
            label
            for item in series
            for label in item
            if label in {"repository", "run_id", "source_sha", "source_ref"}
        }
    )

    time.sleep(2)
    emit(args.otlp_endpoint, "healthy")
    healthy_values = {
        "duration": _wait_scalar(
            args.prometheus_url,
            'ternforge_update_processing_duration_seconds{ternforge_trigger="release"}',
            180,
        ),
        "success": _wait_scalar(
            args.prometheus_url,
            'ternforge_update_run_success{ternforge_trigger="release"}',
            1,
        ),
        "coverage_gap": _wait_scalar(
            args.prometheus_url,
            'abs(ternforge_fleet_expected_repositories{ternforge_trigger="release"} - ternforge_fleet_observed_repositories{ternforge_trigger="release"})',
            0,
        ),
        "token_scope_ok": _wait_scalar(
            args.prometheus_url,
            'ternforge_fleet_token_scope_ok{ternforge_trigger="release"}',
            1,
        ),
    }
    fresh_seconds = _scalar(
        args.prometheus_url,
        'time() - ternforge_update_last_success_unixtime{ternforge_trigger="release"}',
    )
    healthy_alerts, healthy_alert_observation = _wait_alerts(args.grafana_url, set())

    status, rules = _request(args.grafana_url.rstrip("/") + "/api/v1/provisioning/alert-rules")
    provisioned_text = json.dumps(rules).lower()
    provisioned_uids = {uid for uid in ALERT_UIDS if uid in provisioned_text}

    summary = {
        "schema_version": 1,
        "contract": {
            "metrics": sorted({item.get("__name__", "") for item in series}),
            "trigger_values": triggers,
            "series_count": len(series),
            "forbidden_high_cardinality_labels": forbidden_labels,
        },
        "unhealthy": {
            "values": unhealthy_values,
            "freshness_seconds": stale_seconds,
            "firing_alerts": sorted(unhealthy_alerts),
        },
        "healthy": {
            "values": healthy_values,
            "freshness_seconds": fresh_seconds,
            "firing_alerts": sorted(healthy_alerts),
        },
        "grafana": {
            "alert_rules_http_status": status,
            "provisioned_alert_uids": sorted(provisioned_uids),
        },
    }
    summary["assertions"] = {
        "all_alert_rules_provisioned": provisioned_uids == ALERT_UIDS,
        "all_unhealthy_alerts_fired": unhealthy_alerts == ALERT_UIDS,
        "all_alerts_resolved": healthy_alerts == set(),
        "trigger_cardinality_bounded": triggers == ["manual", "nightly", "release"],
        "no_high_cardinality_labels": not forbidden_labels,
        "series_count_bounded": len(series) <= 20,
        "stale_signal_exceeded_window": stale_seconds is not None and stale_seconds > 129_600,
        "fresh_signal_within_window": fresh_seconds is not None and fresh_seconds < 60,
    }
    _write_json(output_dir / "summary.json", summary)
    _write_json(output_dir / "unhealthy-alert-state.json", unhealthy_alert_observation)
    _write_json(output_dir / "healthy-alert-state.json", healthy_alert_observation)

    failed = [name for name, passed in summary["assertions"].items() if not passed]
    if failed:
        raise SystemExit("failed assertions: " + ", ".join(failed))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--otlp-endpoint", default="http://127.0.0.1:4318")
    parser.add_argument("--prometheus-url", default="http://127.0.0.1:9090")
    parser.add_argument("--grafana-url", default="http://127.0.0.1:3000")
    args = parser.parse_args()
    validate(args)


if __name__ == "__main__":
    main()
