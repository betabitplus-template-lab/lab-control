"""Checks for focused architecture docs shaped by vertical_slice_doc_template.md."""

from __future__ import annotations

from pathlib import Path

from _shared.context import CheckSpec, ErrorSink, ProjectContext
from _shared.markdown import (
    require_diagram_question_and_mermaid,
    require_heading_order,
    require_overview_start,
    require_section_subheadings,
    top_level_headings,
)


def _select_concept_paths(context: ProjectContext) -> list[Path]:
    return context.doc_glob("architecture/concepts/*.md", exclude_names=("README.md",))


def _check_concept_file(
    context: ProjectContext,
    path: Path,
    errors: ErrorSink,
) -> None:
    text = context.read_text(path)
    headings = top_level_headings(text)
    require_overview_start(context, path, text, errors)
    require_diagram_question_and_mermaid(context, path, text, errors)
    require_heading_order(
        context,
        path,
        headings,
        ["Overview", "Main Model", "Rules"],
        errors,
    )
    require_section_subheadings(
        context,
        path,
        text,
        "Main Model",
        errors,
    )


def _select_flow_paths(context: ProjectContext) -> list[Path]:
    return context.doc_glob("architecture/flows/*.md", exclude_names=("README.md",))


def _check_flow_file(
    context: ProjectContext,
    path: Path,
    errors: ErrorSink,
) -> None:
    text = context.read_text(path)
    headings = top_level_headings(text)
    require_overview_start(context, path, text, errors)
    require_diagram_question_and_mermaid(context, path, text, errors)
    require_heading_order(
        context,
        path,
        headings,
        ["Overview", "Main Flow", "Rules"],
        errors,
    )


SPECS = (
    CheckSpec(
        "docs.vertical_slice_doc_template.concepts",
        _select_concept_paths,
        _check_concept_file,
    ),
    CheckSpec(
        "docs.vertical_slice_doc_template.flows",
        _select_flow_paths,
        _check_flow_file,
    ),
)
