"""Checks for proof docs shaped by verification_doc_template.md."""

from __future__ import annotations

from pathlib import Path

from _shared.context import CheckSpec, ErrorSink, ProjectContext
from _shared.markdown import (
    heading_count,
    require_diagram_question_and_mermaid,
    require_heading_order,
    require_numbered_heading_prefix,
    require_numbered_labeled_block_line_prefix,
    require_numbered_section_line_prefix,
    require_numbered_subsection_description_prefix,
    require_overview_start,
    top_level_headings,
)
from _shared.reporting import expect


def _select_proof_docs(context: ProjectContext) -> list[Path]:
    return context.doc_glob("verification/e2e/*.md", exclude_names=("README.md",))


def _check_proof_doc(
    context: ProjectContext,
    path: Path,
    errors: ErrorSink,
) -> None:
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
        ["Overview", "Proof Areas"],
        errors,
    )
    expect(
        context,
        path,
        heading_count(text, r"^## \d+\. ")
        == heading_count(text, r"^### Seen In Tests$"),
        (
            "each numbered proof area should contain exactly one "
            "`### Seen In Tests` subsection"
        ),
        errors,
    )
    require_numbered_heading_prefix(context, path, text, "Proof: ", errors)
    require_numbered_section_line_prefix(
        context,
        path,
        text,
        (0, "This proof area shows that "),
        errors=errors,
    )
    require_numbered_subsection_description_prefix(
        context,
        path,
        text,
        ("Seen In Tests", "proves "),
        errors,
    )
    require_numbered_labeled_block_line_prefix(
        context,
        path,
        text,
        ("Walkthrough", 0, "1. "),
        errors,
    )
    require_numbered_labeled_block_line_prefix(
        context,
        path,
        text,
        ("Why this is sufficient", 0, "- "),
        errors,
    )
    require_numbered_labeled_block_line_prefix(
        context,
        path,
        text,
        ("Would fail if", 0, "- "),
        errors,
    )


def _select_workbench_overview(context: ProjectContext) -> list[Path]:
    return context.doc_paths("verification/workbench.md")


def _check_workbench_overview(
    context: ProjectContext,
    path: Path,
    errors: ErrorSink,
) -> None:
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
    required_headings = ["Overview"]
    if "Provider Suites" in headings:
        required_headings.append("Provider Suites")
    required_headings.append("Proof Areas")
    require_heading_order(
        context,
        path,
        headings,
        required_headings,
        errors,
    )
    expect(
        context,
        path,
        heading_count(text, r"^## \d+\. ")
        == heading_count(text, r"^### Seen In Scripts$"),
        (
            "each numbered workbench area should contain exactly one "
            "`### Seen In Scripts` subsection"
        ),
        errors,
    )
    require_numbered_heading_prefix(context, path, text, "Proof: ", errors)
    require_numbered_section_line_prefix(
        context,
        path,
        text,
        (0, "This proof area shows that "),
        errors=errors,
    )
    require_numbered_subsection_description_prefix(
        context,
        path,
        text,
        ("Seen In Scripts", "proves "),
        errors,
    )


SPECS = (
    CheckSpec(
        "verification.verification_doc_template",
        _select_proof_docs,
        _check_proof_doc,
    ),
    CheckSpec(
        "verification.verification_doc_template.workbench",
        _select_workbench_overview,
        _check_workbench_overview,
    ),
)
