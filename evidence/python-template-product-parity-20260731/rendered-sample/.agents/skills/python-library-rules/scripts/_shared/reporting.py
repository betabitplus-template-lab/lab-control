"""Shared reporting helpers for template checkers."""

from __future__ import annotations

from pathlib import Path

from _shared.context import ErrorSink, ProjectContext


def expect(
    context: ProjectContext,
    path: Path,
    predicate: object,
    message: str,
    errors: ErrorSink,
) -> None:
    """Append one repo-relative error when a predicate fails."""
    if not predicate:
        errors.append(f"{context.display_path(path)}: {message}")
