"""Shared runner for reference-template check specs."""

from __future__ import annotations

from collections.abc import Iterable

from _shared.context import CheckSpec, ProjectContext


def run_specs(context: ProjectContext, specs: Iterable[CheckSpec]) -> list[str]:
    """Run all registered specs and collect their errors."""
    errors: list[str] = []
    for spec in specs:
        for path in spec.select_paths(context):
            spec.check_file(context, path, errors)
    return errors
