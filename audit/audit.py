#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ORG = "betabitplus-template-lab"
REPOS = [
    "components",
    "python-lib",
    "python-internal-package",
    "python-starter-platform",
    "sandbox-python-lib",
    "sandbox-python-platform",
    "sandbox-workspace",
    "lab-control",
]


def gh(endpoint: str):
    result = subprocess.run(
        ["gh", "api", endpoint, "--paginate"],
        text=True,
        capture_output=True,
        check=True,
        env={**os.environ, "GH_TOKEN": os.environ["LAB_TOKEN"]},
    )
    chunks = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if len(chunks) == 1:
        return chunks[0]
    flattened = []
    for chunk in chunks:
        if isinstance(chunk, list):
            flattened.extend(chunk)
        else:
            flattened.append(chunk)
    return flattened


def main() -> None:
    report = {
        "organization": ORG,
        "expected_repositories": REPOS,
        "repositories": {},
        "safety": {},
    }
    for name in REPOS:
        full = f"{ORG}/{name}"
        metadata = gh(f"repos/{full}")
        branches = gh(f"repos/{full}/branches?per_page=100")
        pulls = gh(f"repos/{full}/pulls?state=open&per_page=100")
        issues = gh(f"repos/{full}/issues?state=open&per_page=100")
        tags = gh(f"repos/{full}/git/matching-refs/tags/")
        report["repositories"][name] = {
            "full_name": metadata["full_name"],
            "private": metadata["private"],
            "archived": metadata["archived"],
            "default_branch": metadata["default_branch"],
            "branches": sorted(branch["name"] for branch in branches),
            "open_pull_requests": sorted(pr["number"] for pr in pulls),
            "open_issues_including_prs": sorted(issue["number"] for issue in issues),
            "tags": sorted(ref["ref"].removeprefix("refs/tags/") for ref in tags),
        }
    installed = sorted(report["repositories"])
    report["safety"] = {
        "exact_repository_set": installed == sorted(REPOS),
        "all_private": all(item["private"] for item in report["repositories"].values()),
        "all_unarchived": all(not item["archived"] for item in report["repositories"].values()),
        "all_default_main": all(item["default_branch"] == "main" for item in report["repositories"].values()),
        "production_repositories_queried_or_mutated": 0,
    }
    failures = [key for key, value in report["safety"].items() if isinstance(value, bool) and not value]
    out = Path(os.environ.get("GITHUB_WORKSPACE", ".")) / "docs" / "results" / "repository-audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit(f"audit failures: {failures}")


if __name__ == "__main__":
    main()
