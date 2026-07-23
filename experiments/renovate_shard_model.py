#!/usr/bin/env python3
"""Deterministic shard and inventory validation experiment for Ternforge."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Profile:
    name: str
    update_sources: frozenset[str]


def shard_for(repository: str, shard_count: int) -> int:
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    digest = hashlib.sha256(repository.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % shard_count


def validate_inventory(
    entries: list[dict[str, str]], profiles: dict[str, Profile], known_sources: set[str]
) -> None:
    repositories = [entry.get("repository", "") for entry in entries]
    if any(not repository or "/" not in repository for repository in repositories):
        raise ValueError("every repository must be a non-empty owner/name")
    if len(repositories) != len(set(repositories)):
        raise ValueError("repository names must be unique")
    for entry in entries:
        profile_name = entry.get("profile", "")
        if profile_name not in profiles:
            raise ValueError(f"unknown profile: {profile_name}")
        sources = profiles[profile_name].update_sources
        if not sources:
            raise ValueError(f"profile has no update sources: {profile_name}")
        unknown = sources - known_sources
        if unknown:
            raise ValueError(f"unknown update sources: {sorted(unknown)}")


def targets_for_source(
    entries: list[dict[str, str]], profiles: dict[str, Profile], source: str
) -> list[str]:
    return sorted(
        entry["repository"]
        for entry in entries
        if source in profiles[entry["profile"]].update_sources
    )


def group_targets(targets: Iterable[str], shard_count: int) -> dict[int, list[str]]:
    grouped: dict[int, list[str]] = {}
    for repository in sorted(targets):
        grouped.setdefault(shard_for(repository, shard_count), []).append(repository)
    return grouped


def build_fleet(size: int) -> list[dict[str, str]]:
    return [
        {
            "repository": f"betabitplus-template-lab/generated-{index:05d}",
            "profile": "python" if index % 5 else "infra",
        }
        for index in range(size)
    ]


def require_invalid(
    entries: list[dict[str, str]], profiles: dict[str, Profile], known_sources: set[str]
) -> str:
    try:
        validate_inventory(entries, profiles, known_sources)
    except ValueError as error:
        return str(error)
    raise AssertionError("invalid inventory unexpectedly passed")


def scenario(size: int, shard_count: int) -> dict[str, object]:
    profiles = {
        "python": Profile("python", frozenset({"template", "infra-ci"})),
        "infra": Profile("infra", frozenset({"infra-template", "infra-ci"})),
    }
    sources = {"template", "infra-template", "infra-ci"}
    inventory = build_fleet(size)
    validate_inventory(inventory, profiles, sources)

    targets = targets_for_source(inventory, profiles, "infra-ci")
    grouped = group_targets(targets, shard_count)
    counts = Counter({shard: len(repositories) for shard, repositories in grouped.items()})

    shuffled = list(inventory)
    random.Random(20260723).shuffle(shuffled)
    stable = group_targets(
        targets_for_source(shuffled, profiles, "infra-ci"), shard_count
    ) == grouped
    assert stable
    assert len(grouped) <= shard_count < 256
    assert sum(counts.values()) == size
    assert max(counts.values()) < 500

    mean = size / shard_count
    max_deviation = max(abs(count - mean) for count in counts.values()) / mean
    return {
        "fleet_size": size,
        "shard_count": shard_count,
        "non_empty_jobs": len(grouped),
        "min_repositories_per_shard": min(counts.values()),
        "max_repositories_per_shard": max(counts.values()),
        "mean_repositories_per_shard": mean,
        "max_relative_deviation": round(max_deviation, 4),
        "matrix_under_256": len(grouped) < 256,
        "token_scope_under_500": max(counts.values()) < 500,
        "stable_across_input_order": stable,
        "assignment_sample": {
            repository: shard_for(repository, shard_count)
            for repository in sorted(targets)[:5]
        },
    }


def main() -> None:
    profiles = {
        "python": Profile("python", frozenset({"template"})),
    }
    known_sources = {"template"}
    valid = [{"repository": "owner/repository", "profile": "python"}]
    validate_inventory(valid, profiles, known_sources)

    invalid_results = {
        "duplicate_repository": require_invalid(valid + valid, profiles, known_sources),
        "unknown_profile": require_invalid(
            [{"repository": "owner/repository", "profile": "missing"}],
            profiles,
            known_sources,
        ),
        "unknown_source": require_invalid(
            valid,
            {"python": Profile("python", frozenset({"missing"}))},
            known_sources,
        ),
        "empty_sources": require_invalid(
            valid,
            {"python": Profile("python", frozenset())},
            known_sources,
        ),
    }

    evidence = {
        "algorithm": "sha256(repository)[0:8] mod shard_count",
        "scenarios": [scenario(1000, 8), scenario(5000, 32)],
        "invalid_inventory_rejections": invalid_results,
    }
    output = Path(__file__).resolve().parents[1] / "evidence" / "renovate-shards.json"
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
