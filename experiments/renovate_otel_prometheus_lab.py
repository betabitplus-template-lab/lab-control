#!/usr/bin/env python3
"""Collect evidence from a Prometheus OTLP backend after one Renovate run."""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def request_json(base_url: str, path: str, params: dict[str, str] | None = None) -> Any:
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(base_url.rstrip("/") + path + query, timeout=15) as response:
        payload = json.load(response)
    if payload.get("status") != "success":
        raise RuntimeError(f"Prometheus request failed: {payload}")
    return payload["data"]


def instant_query(base_url: str, expression: str) -> float | None:
    data = request_json(base_url, "/api/v1/query", {"query": expression})
    result = data.get("result", [])
    if not result:
        return None
    value = result[0].get("value")
    if not isinstance(value, list) or len(value) != 2:
        return None
    raw = value[1]
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def metric_names(base_url: str) -> list[str]:
    values = request_json(base_url, "/api/v1/label/__name__/values")
    return sorted(name for name in values if name.startswith("traces_span_metrics_"))


def label_values(base_url: str, label: str) -> list[str]:
    try:
        values = request_json(base_url, f"/api/v1/label/{urllib.parse.quote(label)}/values")
    except Exception:
        return []
    return sorted(values)


def find_metric(names: list[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"expected one metric ending with {suffix!r}, found {matches}")
    return matches[0]


def wait_for_repository_spans(
    base_url: str,
    calls_metric: str,
    expected_repositories: int,
    timeout_seconds: int,
) -> float:
    expression = f'sum({calls_metric}{{span_name="repository"}})'
    deadline = time.monotonic() + timeout_seconds
    while True:
        value = instant_query(base_url, expression) or 0.0
        if value >= expected_repositories:
            return value
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"timed out waiting for {expected_repositories} repository spans; observed {value}"
            )
        time.sleep(2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prometheus-url", default="http://127.0.0.1:9090")
    parser.add_argument("--expected-repositories", type=int, required=True)
    parser.add_argument("--control-seconds", type=float, required=True)
    parser.add_argument("--instrumented-seconds", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args()

    names: list[str] = []
    deadline = time.monotonic() + args.timeout_seconds
    while not names:
        names = metric_names(args.prometheus_url)
        if names:
            break
        if time.monotonic() >= deadline:
            raise RuntimeError("no span metrics appeared in Prometheus")
        time.sleep(2)

    calls_metric = find_metric(names, "calls_total")
    duration_sum_metric = find_metric(names, "duration_milliseconds_sum")
    duration_count_metric = find_metric(names, "duration_milliseconds_count")
    duration_bucket_metric = find_metric(names, "duration_milliseconds_bucket")

    repository_calls = wait_for_repository_spans(
        args.prometheus_url,
        calls_metric,
        args.expected_repositories,
        args.timeout_seconds,
    )
    run_calls = instant_query(
        args.prometheus_url, f'sum({calls_metric}{{span_name="run"}})'
    )
    run_duration_count = instant_query(
        args.prometheus_url, f'sum({duration_count_metric}{{span_name="run"}})'
    )
    run_duration_ms = instant_query(
        args.prometheus_url,
        f'sum({duration_sum_metric}{{span_name="run"}}) '
        f'/ sum({duration_count_metric}{{span_name="run"}})',
    )
    repository_p95_ms = instant_query(
        args.prometheus_url,
        "histogram_quantile(0.95, "
        f'sum by (le) ({duration_bucket_metric}{{span_name="repository"}}))',
    )
    span_metric_series = instant_query(
        args.prometheus_url,
        'count({__name__=~"traces_span_metrics_.*"})',
    )

    span_names = label_values(args.prometheus_url, "span_name")
    allowed_span_names = {
        "run",
        "repository",
        "init",
        "onboarding",
        "extract",
        "lookup",
        "update",
    }

    overhead_seconds = args.instrumented_seconds - args.control_seconds
    overhead_ratio = (
        args.instrumented_seconds / args.control_seconds
        if args.control_seconds > 0
        else None
    )
    result = {
        "expected_repositories": args.expected_repositories,
        "control_seconds": args.control_seconds,
        "instrumented_seconds": args.instrumented_seconds,
        "instrumentation_overhead_seconds": overhead_seconds,
        "instrumentation_duration_ratio": overhead_ratio,
        "metrics": {
            "names": names,
            "series_count": span_metric_series,
            "repository_calls": repository_calls,
            "run_calls": run_calls,
            "run_duration_count": run_duration_count,
            "run_duration_ms": run_duration_ms,
            "repository_p95_ms": repository_p95_ms,
            "span_names": span_names,
            "renovate_splits": label_values(args.prometheus_url, "renovate_split"),
            "service_names": label_values(args.prometheus_url, "service_name"),
        },
        "assertions": {
            "all_repositories_observed": repository_calls >= args.expected_repositories,
            "run_span_observed": bool(
                run_duration_count and run_duration_count >= 1
            ),
            "run_duration_observed": run_duration_ms is not None and run_duration_ms > 0,
            "repository_p95_observed": repository_p95_ms is not None
            and repository_p95_ms > 0,
            "only_bounded_span_names": set(span_names).issubset(allowed_span_names),
            "bounded_series_for_lab": span_metric_series is not None
            and span_metric_series < 300,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))

    failed = [name for name, passed in result["assertions"].items() if not passed]
    if failed:
        raise SystemExit(f"failed assertions: {', '.join(failed)}")


if __name__ == "__main__":
    main()
