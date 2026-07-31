"""Checks for property-testing docs shaped by property_based_testing_doc_template.md."""

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
    return context.doc_paths("verification/property-based-testing.md")


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
        [
            "Overview",
            "Testing Role",
            "Target Areas",
            "Rules",
        ],
        errors,
    )
    expect(
        context,
        path,
        heading_count(text, r"^## \d+\. ")
        == heading_count(text, r"^### Good Targets$"),
        (
            "each numbered strategy area should contain exactly one "
            "`### Good Targets` subsection"
        ),
        errors,
    )
    require_numbered_heading_prefix(context, path, text, "Area: ", errors)
    require_numbered_section_line_prefix(
        context,
        path,
        text,
        (0, "This area should "),
        errors=errors,
    )


SPECS = (
    CheckSpec(
        "verification.property_based_testing_doc_template",
        _select_paths,
        _check_file,
    ),
)
