"""Checks for dependency docs shaped by dependencies_doc_template.md."""

from __future__ import annotations

from pathlib import Path

from _shared.context import CheckSpec, ErrorSink, ProjectContext
from _shared.markdown import (
    require_diagram_question_and_mermaid,
    require_heading_order,
    require_overview_start,
    top_level_headings,
)
from _shared.reporting import expect

_CORE_HEADINGS = ("Dependency Roles", "Dependency Groups")


def _select_paths(context: ProjectContext) -> list[Path]:
    return context.doc_paths("dependencies.md")


def _check_file(context: ProjectContext, path: Path, errors: ErrorSink) -> None:
    text = context.read_text(path)
    headings = top_level_headings(text)
    require_overview_start(context, path, text, errors)
    require_diagram_question_and_mermaid(
        context,
        path,
        text,
        errors,
        required=False,
    )
    core = next((heading for heading in _CORE_HEADINGS if heading in headings), None)
    expect(context, path, core is not None, "missing dependency core section", errors)
    if core is not None:
        require_heading_order(
            context,
            path,
            headings,
            ["Overview", core, "Rules"],
            errors,
        )


SPECS = (CheckSpec("docs.dependencies_doc_template", _select_paths, _check_file),)
