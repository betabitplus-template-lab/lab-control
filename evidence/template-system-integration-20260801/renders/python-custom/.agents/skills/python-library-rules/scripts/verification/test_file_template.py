"""Checks for ordinary pytest files shaped by test_file_template.md."""

from __future__ import annotations

from pathlib import Path

from _shared.context import CheckSpec, ErrorSink, ProjectContext
from _shared.python_source import (
    require_module_docstring,
    require_section_order,
    section_titles,
)
from _shared.reporting import expect

_ALLOWED_SECTIONS = {
    "Scenario",
    "Strategies",
    "Fixtures",
    "Helpers",
    "Assertions",
    "Properties",
    "Tests",
}


def _select_paths(context: ProjectContext) -> list[Path]:
    return [
        path for path in context.tests_glob("**/test_*.py") if "e2e" not in path.parts
    ]


def _check_file(context: ProjectContext, path: Path, errors: ErrorSink) -> None:
    text = context.read_text(path)
    require_module_docstring(context, path, text, errors)
    titles = section_titles(text)
    for title in titles:
        expect(
            context,
            path,
            title in _ALLOWED_SECTIONS,
            f"`{title}` is not an allowed standard section title",
            errors,
        )
    if "Properties" in titles and "Tests" in titles:
        require_section_order(context, path, text, ["Properties", "Tests"], errors)
    expect(
        context,
        path,
        "Properties" in titles or "Tests" in titles,
        "test file should include `Properties` and/or `Tests`",
        errors,
    )


SPECS = (CheckSpec("verification.test_file_template", _select_paths, _check_file),)
