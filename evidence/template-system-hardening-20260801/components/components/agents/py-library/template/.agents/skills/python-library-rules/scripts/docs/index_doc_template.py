"""Checks for index docs shaped by index_doc_template.md."""

from __future__ import annotations

from pathlib import Path

from _shared.context import CheckSpec, ErrorSink, ProjectContext
from _shared.markdown import (
    require_index_descriptions,
    require_index_overview_shape,
    require_no_diagram,
    require_overview_start,
)


def _select_paths(context: ProjectContext) -> list[Path]:
    return context.doc_glob("**/README.md")


def _check_file(
    context: ProjectContext,
    path: Path,
    errors: ErrorSink,
) -> None:
    text = context.read_text(path)
    require_overview_start(context, path, text, errors)
    require_index_overview_shape(context, path, text, errors)
    require_no_diagram(context, path, text, errors)
    require_index_descriptions(context, path, text, errors)


SPECS = (CheckSpec("docs.index_doc_template", _select_paths, _check_file),)
