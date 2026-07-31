"""Checks for executable e2e files shaped by e2e_test_template.md."""

from __future__ import annotations

from pathlib import Path

from _shared.context import CheckSpec, ErrorSink, ProjectContext
from _shared.python_source import (
    require_first_nonempty_line,
    require_module_docstring,
    require_section_order,
    require_top_level_function,
)
from _shared.reporting import expect


def _select_paths(context: ProjectContext) -> list[Path]:
    return context.tests_glob("**/e2e/**/test_*.py")


def _check_file(context: ProjectContext, path: Path, errors: ErrorSink) -> None:
    text = context.read_text(path)
    require_first_nonempty_line(context, path, text, "# %%", errors)
    require_module_docstring(context, path, text, errors)
    expect(context, path, "pytestmark" in text, "missing `pytestmark`", errors)
    require_section_order(
        context,
        path,
        text,
        [
            "Scenario",
            "Helpers",
            "Pipeline",
            "Assertions",
            "Tests",
            "Demo (Manual Execution)",
        ],
        errors,
    )
    require_top_level_function(context, path, text, "main", errors)


SPECS = (CheckSpec("verification.e2e_test_template", _select_paths, _check_file),)
