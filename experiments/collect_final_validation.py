#!/usr/bin/env python3
"""Collect immutable GitHub evidence for the final Ternforge lab validation."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNS: list[tuple[str, str, int, str]] = [
    ("scalr_positive", "betabitplus-template-lab/sandbox-ternforge-scalr-oidc-20260723-r1", 29996537630, "success"),
    ("scalr_wrong_audience", "betabitplus-template-lab/sandbox-ternforge-scalr-oidc-20260723-r1", 29996589078, "success"),
    ("scalr_without_id_token_permission", "betabitplus-template-lab/sandbox-ternforge-scalr-oidc-20260723-r1", 29996591159, "success"),
    ("scalr_wrong_repository", "betabitplus-template-lab/sandbox-ternforge-scalr-oidc-denied-20260723-r1", 29996593517, "success"),
    ("scalr_rbac_scope", "betabitplus-template-lab/sandbox-ternforge-scalr-oidc-20260723-r1", 29996924657, "success"),
    ("scalr_state_lock", "betabitplus-template-lab/sandbox-ternforge-scalr-oidc-20260723-r1", 29996927248, "success"),
    ("scalr_token_expiry", "betabitplus-template-lab/sandbox-ternforge-scalr-oidc-20260723-r1", 30001478357, "success"),
    ("publisher_create", "betabitplus-template-lab/sandbox-ternforge-final-contract-20260723-r1", 29998051274, "success"),
    ("publisher_idempotent", "betabitplus-template-lab/sandbox-ternforge-final-contract-20260723-r1", 29998084474, "success"),
    ("publisher_wrong_tag", "betabitplus-template-lab/sandbox-ternforge-final-contract-20260723-r1", 29998222773, "failure"),
    ("promotion_non_dev_source", "betabitplus-template-lab/sandbox-ternforge-final-contract-20260723-r1", 29998289790, "failure"),
    ("promotion_stale_head", "betabitplus-template-lab/sandbox-ternforge-promotion-negative-20260723-r1", 29998364612, "failure"),
    ("promotion_current_head", "betabitplus-template-lab/sandbox-ternforge-promotion-negative-20260723-r1", 29998382370, "success"),
    ("router_model", "betabitplus-template-lab/lab-control", 29998637015, "success"),
    ("dispatch_boundary", "betabitplus-template-lab/lab-control", 29998914668, "success"),
    ("dispatch_target", "betabitplus-template-lab/sandbox-ternforge-dispatch-target-20260723-r1", 29998924315, "success"),
    ("renovate_token_boundary", "betabitplus-template-lab/lab-control", 29999042911, "success"),
]

FINAL_REPOSITORY = "betabitplus-template-lab/sandbox-ternforge-final-contract-20260723-r1"


def gh(*args: str) -> str:
    return subprocess.check_output(["gh", *args], text=True).strip()


def gh_json(*args: str) -> Any:
    return json.loads(gh(*args))


def collect_run(
    name: str, repository: str, run_id: int, expected_conclusion: str
) -> dict[str, Any]:
    data = gh_json(
        "run",
        "view",
        str(run_id),
        "--repo",
        repository,
        "--json",
        "name,displayTitle,event,status,conclusion,createdAt,updatedAt,headSha,url,jobs",
    )
    jobs = [
        {
            "name": job["name"],
            "status": job["status"],
            "conclusion": job["conclusion"],
            "started_at": job["startedAt"],
            "completed_at": job["completedAt"],
            "url": job["url"],
        }
        for job in data["jobs"]
    ]
    return {
        "name": name,
        "repository": repository,
        "run_id": run_id,
        "workflow": data["name"],
        "display_title": data["displayTitle"],
        "event": data["event"],
        "status": data["status"],
        "conclusion": data["conclusion"],
        "expected_conclusion": expected_conclusion,
        "matches_expected_conclusion": data["conclusion"] == expected_conclusion,
        "created_at": data["createdAt"],
        "updated_at": data["updatedAt"],
        "head_sha": data["headSha"],
        "url": data["url"],
        "jobs": jobs,
    }


def main() -> None:
    runs = [collect_run(*spec) for spec in RUNS]

    rulesets = gh_json("api", f"repos/{FINAL_REPOSITORY}/rulesets")
    ruleset_details = [
        gh_json("api", f"repos/{FINAL_REPOSITORY}/rulesets/{ruleset['id']}")
        for ruleset in rulesets
    ]

    main_sha = gh(
        "api",
        f"repos/{FINAL_REPOSITORY}/git/ref/heads/main",
        "--jq",
        ".object.sha",
    )
    main_commit = gh_json("api", f"repos/{FINAL_REPOSITORY}/commits/{main_sha}")
    promoted_sha = main_commit["parents"][1]["sha"]
    v030_tag_sha = gh(
        "api",
        f"repos/{FINAL_REPOSITORY}/git/ref/tags/v0.3.0",
        "--jq",
        ".object.sha",
    )
    v040_tag_sha = gh(
        "api",
        f"repos/{FINAL_REPOSITORY}/git/ref/tags/v0.4.0",
        "--jq",
        ".object.sha",
    )
    release = gh_json(
        "release",
        "view",
        "v0.3.0",
        "--repo",
        FINAL_REPOSITORY,
        "--json",
        "tagName,targetCommitish,createdAt,publishedAt,body,url",
    )

    evidence = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs": runs,
        "all_runs_match_expected_conclusion": all(
            run["matches_expected_conclusion"] for run in runs
        ),
        "final_repository": {
            "repository": FINAL_REPOSITORY,
            "main_sha": main_sha,
            "current_promoted_sha": promoted_sha,
            "v0.3.0_tag_sha": v030_tag_sha,
            "v0.3.0_release": release,
            "v0.3.0_tag_matches_release": v030_tag_sha == release["targetCommitish"],
            "v0.4.0_tag_sha": v040_tag_sha,
            "v0.4.0_tag_mismatches_current_promoted_sha": v040_tag_sha != promoted_sha,
            "rulesets": ruleset_details,
        },
    }

    output = Path(__file__).resolve().parents[1] / "evidence" / "final-validation-runs.json"
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
