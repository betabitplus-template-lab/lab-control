"""Checks for principles docs shaped by principles_doc_template.md."""

from __future__ import annotations

from pathlib import Path

from _shared.context import CheckSpec, ErrorSink, ProjectContext
from _shared.markdown import (
    require_no_diagram,
    require_overview_start,
    top_level_headings,
)
from _shared.reporting import expect


def _select_paths(context: ProjectContext) -> list[Path]:
    return context.doc_glob(
        "architecture/principles/*.md",
        exclude_names=("README.md",),
    )


def _check_file(context: ProjectContext, path: Path, errors: ErrorSink) -> None:
    text = context.read_text(path)
    headings = top_level_headings(text)
    require_overview_start(context, path, text, errors)
    require_no_diagram(context, path, text, errors)
    expect(
        context,
        path,
        "Refactor Checks" not in headings,
        "principles docs should not use `Refactor Checks`",
        errors,
    )
    has_rules = "Rules" in headings
    has_named_sections = any(
        heading not in {"Overview", "Rules", "Invariants"} for heading in headings
    )
    expect(
        context,
        path,
        has_rules or has_named_sections,
        "principles docs should use `Rules` or named principle sections",
        errors,
    )


SPECS = (CheckSpec("docs.principles_doc_template", _select_paths, _check_file),)
