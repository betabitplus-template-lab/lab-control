#!/usr/bin/env python3
"""Prepare and summarize the full-fleet Renovate scaling experiment."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_order(names: list[str]) -> list[str]:
    return sorted(
        names,
        key=lambda name: (hashlib.sha256(name.encode("utf-8")).hexdigest(), name),
    )


def command_matrix(args: argparse.Namespace) -> None:
    sizes = json.loads(args.sizes)
    if not isinstance(sizes, list) or not sizes or not all(isinstance(size, int) for size in sizes):
        raise SystemExit("sizes must be a non-empty JSON array of integers")
    if any(size <= 0 for size in sizes):
        raise SystemExit("sizes must contain only positive integers")
    value = json.dumps(sorted(set(sizes)), separators=(",", ":"))
    with Path(args.github_output).open("a", encoding="utf-8") as handle:
        handle.write(f"sizes={value}\n")


def command_select(args: argparse.Namespace) -> None:
    inventory = read_json(args.inventory)
    if not isinstance(inventory, list) or not all(isinstance(name, str) for name in inventory):
        raise SystemExit("inventory must be a JSON array of repository names")
    if len(set(inventory)) != len(inventory):
        raise SystemExit("inventory contains duplicate repository names")
    ordered = stable_order(inventory)
    if args.size > len(ordered):
        raise SystemExit(f"requested {args.size} repositories, inventory contains {len(ordered)}")
    selected = ordered[: args.size]
    output = {
        "inventory_count": len(inventory),
        "selection_method": "sha256(repository-name), ascending",
        "requested_size": args.size,
        "repositories": selected,
    }
    write_json(args.output, output)
    with Path(args.github_output).open("a", encoding="utf-8") as handle:
        handle.write(
            "repositories_json="
            + json.dumps(selected, separators=(",", ":"))
            + "\n"
        )
        handle.write("repositories<<EOF\n")
        handle.write("\n".join(selected) + "\n")
        handle.write("EOF\n")


def percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return ordered[index]


def parse_rate(path: str | None) -> dict[str, int | None]:
    if not path or not Path(path).exists():
        return {"limit": None, "remaining": None, "used": None}
    payload = read_json(path)
    core = payload.get("resources", {}).get("core", {})
    return {
        "limit": core.get("limit"),
        "remaining": core.get("remaining"),
        "used": core.get("used"),
    }


def parse_log(path: str | Path) -> dict[str, Any]:
    repositories: set[str] = set()
    timings: dict[str, int] = {}
    timing_splits: dict[str, dict[str, int]] = {}
    warning_count = 0
    error_count = 0
    http_request_count = 0
    invalid_json_lines = 0

    for raw_line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            invalid_json_lines += 1
            continue
        if not isinstance(record, dict):
            continue

        repository = record.get("repository")
        if isinstance(repository, str):
            repositories.add(repository)

        level = record.get("level")
        if isinstance(level, int):
            if level >= 50:
                error_count += 1
            elif level >= 40:
                warning_count += 1

        message = record.get("msg")
        total = record.get("total")
        if (
            isinstance(repository, str)
            and isinstance(message, str)
            and message.startswith("Repository timing splits")
            and isinstance(total, int)
        ):
            timings[repository] = total
            splits = record.get("splits")
            if isinstance(splits, dict):
                timing_splits[repository] = {
                    key: value
                    for key in ("init", "onboarding", "extract", "lookup", "update")
                    if isinstance((value := splits.get(key)), int)
                }

        hosts = record.get("hosts")
        if isinstance(hosts, dict):
            for stats in hosts.values():
                if isinstance(stats, dict) and isinstance(stats.get("count"), int):
                    http_request_count += stats["count"]

    timing_values = list(timings.values())
    phase_sums = {
        phase: sum(splits.get(phase, 0) for splits in timing_splits.values())
        for phase in ("init", "onboarding", "extract", "lookup", "update")
    }
    update_values = [splits.get("update", 0) for splits in timing_splits.values()]
    light_repositories = [
        repository
        for repository, splits in timing_splits.items()
        if splits.get("update", 0) <= 500
    ]
    slowest = [
        {"repository": repository, "total_ms": total_ms}
        for repository, total_ms in sorted(
            timings.items(), key=lambda item: (-item[1], item[0])
        )[:10]
    ]
    return {
        "repositories_seen": len(repositories),
        "repositories_with_timing": len(timings),
        "repository_timing_ms": {
            "p50": percentile(timing_values, 0.50),
            "p95": percentile(timing_values, 0.95),
            "max": max(timing_values) if timing_values else None,
            "sum": sum(timing_values),
        },
        "phase_timing_ms": {
            **phase_sums,
            "total": sum(timing_values),
            "update_share": (
                phase_sums["update"] / sum(timing_values) if timing_values else None
            ),
        },
        "repository_workload": {
            "light_update_at_most_500ms": len(light_repositories),
            "over_5_seconds": sum(value > 5_000 for value in timing_values),
            "over_10_seconds": sum(value > 10_000 for value in timing_values),
            "over_20_seconds": sum(value > 20_000 for value in timing_values),
            "max_update_ms": max(update_values) if update_values else None,
        },
        "slowest_repositories": slowest,
        "warning_count": warning_count,
        "error_count": error_count,
        "http_request_count_from_repository_stats": http_request_count,
        "invalid_json_lines": invalid_json_lines,
    }


def command_summarize(args: argparse.Namespace) -> None:
    parsed = parse_log(args.log)
    before = parse_rate(args.rate_before)
    after = parse_rate(args.rate_after)
    rate_delta = None
    if isinstance(before.get("remaining"), int) and isinstance(after.get("remaining"), int):
        rate_delta = before["remaining"] - after["remaining"]

    elapsed = float(args.elapsed_seconds)
    result = {
        "cohort_size": args.size,
        "phase": args.phase,
        "renovate_exit_status": args.exit_status,
        "scan_elapsed_seconds": elapsed,
        "seconds_per_requested_repository": elapsed / args.size,
        "image_pull_seconds": float(args.image_pull_seconds),
        "github_core_rate_before": before,
        "github_core_rate_after": after,
        "github_core_rate_consumed": rate_delta,
        **parsed,
    }
    write_json(args.output, result)
    print(
        f"| {args.size} | {args.phase} | {elapsed:.1f} | "
        f"{result['seconds_per_requested_repository']:.2f} | "
        f"{parsed['repository_timing_ms']['p95'] or '-'} | "
        f"{rate_delta if rate_delta is not None else '-'} | {args.exit_status} |"
    )


def linear_fit(points: list[tuple[float, float]]) -> dict[str, float | None]:
    if len(points) < 2:
        return {"intercept_seconds": None, "seconds_per_repository": None, "r_squared": None}
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return {"intercept_seconds": None, "seconds_per_repository": None, "r_squared": None}
    slope = sum((x - x_mean) * (y - y_mean) for x, y in points) / denominator
    intercept = y_mean - slope * x_mean
    total = sum((y - y_mean) ** 2 for y in ys)
    residual = sum((y - (intercept + slope * x)) ** 2 for x, y in points)
    r_squared = 1.0 if total == 0 else 1.0 - residual / total
    return {
        "intercept_seconds": intercept,
        "seconds_per_repository": slope,
        "r_squared": r_squared,
    }


def estimated_count(fit: dict[str, float | None], seconds: float) -> int | None:
    intercept = fit.get("intercept_seconds")
    slope = fit.get("seconds_per_repository")
    if not isinstance(intercept, (int, float)) or not isinstance(slope, (int, float)) or slope <= 0:
        return None
    return max(0, math.floor((seconds - intercept) / slope))


def command_combine(args: argparse.Namespace) -> None:
    paths: list[str] = []
    for pattern in args.inputs:
        paths.extend(glob.glob(pattern, recursive=True))
    unique_paths = sorted(set(paths))
    if not unique_paths:
        raise SystemExit("no summary files matched")
    runs = [read_json(path) for path in unique_paths]
    runs.sort(key=lambda item: (item["cohort_size"], item["phase"]))

    cold_points = [
        (float(run["cohort_size"]), float(run["scan_elapsed_seconds"]))
        for run in runs
        if run["phase"] == "cold" and run["renovate_exit_status"] == 0
    ]
    fit = linear_fit(cold_points)
    combined = {
        "runs": runs,
        "cold_scan_linear_fit": fit,
        "estimated_repository_counts": {
            "at_5_minutes": estimated_count(fit, 300),
            "at_15_minutes": estimated_count(fit, 900),
            "at_45_minutes": estimated_count(fit, 2700),
        },
        "limitations": [
            "Estimates are interpolation or extrapolation from this lab fleet, not capacity guarantees.",
            "Repository contents, enabled managers, available updates, lockfile work, API latency, and runner load can change runtime.",
            "The one-hour GitHub App installation-token lifetime remains a hard operational boundary for a single token.",
        ],
    }
    write_json(args.output_json, combined)

    lines = [
        "# Full-fleet Renovate scaling lab",
        "",
        "| Repositories | Phase | Scan seconds | Seconds/repo | Repo p95 ms | GitHub requests | Exit |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for run in runs:
        p95 = run["repository_timing_ms"]["p95"]
        rate = run["github_core_rate_consumed"]
        lines.append(
            f"| {run['cohort_size']} | {run['phase']} | {run['scan_elapsed_seconds']:.1f} | "
            f"{run['seconds_per_requested_repository']:.2f} | {p95 if p95 is not None else '-'} | "
            f"{rate if rate is not None else '-'} | {run['renovate_exit_status']} |"
        )
    lines.extend(
        [
            "",
            "## Cold-scan fit",
            "",
            f"* Fixed overhead: {fit['intercept_seconds']}",
            f"* Seconds per repository: {fit['seconds_per_repository']}",
            f"* R²: {fit['r_squared']}",
            f"* Estimated 5-minute cohort: {combined['estimated_repository_counts']['at_5_minutes']}",
            f"* Estimated 15-minute cohort: {combined['estimated_repository_counts']['at_15_minutes']}",
            f"* Estimated 45-minute cohort: {combined['estimated_repository_counts']['at_45_minutes']}",
            "",
            "These estimates describe this lab fleet only and are not capacity guarantees.",
        ]
    )
    Path(args.output_markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    matrix_parser = subparsers.add_parser("matrix")
    matrix_parser.add_argument("--sizes", required=True)
    matrix_parser.add_argument("--github-output", required=True)
    matrix_parser.set_defaults(func=command_matrix)

    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("--inventory", required=True)
    select_parser.add_argument("--size", type=int, required=True)
    select_parser.add_argument("--output", required=True)
    select_parser.add_argument("--github-output", required=True)
    select_parser.set_defaults(func=command_select)

    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("--log", required=True)
    summarize_parser.add_argument("--size", type=int, required=True)
    summarize_parser.add_argument("--phase", choices=("cold", "warm"), required=True)
    summarize_parser.add_argument("--elapsed-seconds", type=float, required=True)
    summarize_parser.add_argument("--image-pull-seconds", type=float, required=True)
    summarize_parser.add_argument("--exit-status", type=int, required=True)
    summarize_parser.add_argument("--rate-before")
    summarize_parser.add_argument("--rate-after")
    summarize_parser.add_argument("--output", required=True)
    summarize_parser.set_defaults(func=command_summarize)

    combine_parser = subparsers.add_parser("combine")
    combine_parser.add_argument("--inputs", nargs="+", required=True)
    combine_parser.add_argument("--output-json", required=True)
    combine_parser.add_argument("--output-markdown", required=True)
    combine_parser.set_defaults(func=command_combine)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
