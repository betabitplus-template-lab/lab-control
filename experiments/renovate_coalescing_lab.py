#!/usr/bin/env python3
"""Extract one controlled dependency observation from a Renovate JSON log."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterator


def walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def semver_key(value: str) -> tuple[int, int, int, str]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(.*)", value)
    if not match:
        return (-1, -1, -1, value)
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4))


def observe(log_path: Path, dependency: str) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    for raw_line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        for item in walk(record):
            if item.get("depName") != dependency:
                continue
            updates = item.get("updates")
            candidates: list[str] = []
            if isinstance(updates, list):
                for update in updates:
                    if not isinstance(update, dict):
                        continue
                    candidate = update.get("newValue") or update.get("newVersion")
                    if isinstance(candidate, str):
                        candidates.append(candidate)
            observations.append(
                {
                    "current_value": item.get("currentValue"),
                    "current_version": item.get("currentVersion"),
                    "fixed_version": item.get("fixedVersion"),
                    "updates": sorted(set(candidates), key=semver_key),
                }
            )

    if not observations:
        raise SystemExit(f"dependency {dependency!r} was not found in Renovate log")

    with_updates = [item for item in observations if item["updates"]]
    selected = with_updates[-1] if with_updates else observations[-1]
    latest = selected["updates"][-1] if selected["updates"] else selected.get("fixed_version")
    return {**selected, "latest_observed_value": latest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--dependency", required=True)
    parser.add_argument("--event-version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-attempt", required=True)
    args = parser.parse_args()

    result = {
        "event_version": args.event_version,
        "run_id": args.run_id,
        "run_attempt": args.run_attempt,
        **observe(args.log, args.dependency),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if result["latest_observed_value"] != args.event_version:
        raise SystemExit(
            "expected latest value "
            f"{args.event_version!r}, observed {result['latest_observed_value']!r}"
        )

    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
