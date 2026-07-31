"""Checks for usage docs shaped by usage_doc_template.md."""

from __future__ import annotations

from pathlib import Path

from _shared.context import CheckSpec, ErrorSink, ProjectContext
from _shared.markdown import (
    heading_count,
    require_diagram_question_and_mermaid,
    require_heading_order,
    require_numbered_heading_prefix,
    require_numbered_section_line_prefix,
    require_overview_start,
    top_level_headings,
)
from _shared.reporting import expect


def _select_paths(context: ProjectContext) -> list[Path]:
    return context.doc_paths("usage.md")


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
    require_heading_order(
        context,
        path,
        headings,
        ["Overview", "Examples"],
        errors,
    )
    expect(
        context,
        path,
        heading_count(text, r"^## \d+\. ") == text.count("Use when:"),
        "each numbered usage example should contain one `Use when:` block",
        errors,
    )
    require_numbered_heading_prefix(context, path, text, "Pattern: ", errors)
    require_numbered_section_line_prefix(
        context,
        path,
        text,
        (0, "Use when:"),
        errors=errors,
    )
    require_numbered_section_line_prefix(
        context,
        path,
        text,
        (1, "The caller "),
        errors=errors,
    )


SPECS = (CheckSpec("docs.usage_doc_template", _select_paths, _check_file),)
