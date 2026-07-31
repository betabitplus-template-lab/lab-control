"""Checks for workbench files shaped by workbench_script_template.md."""

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
    return context.workbench_glob(
        "**/*.py",
        exclude_names=("__init__.py",),
        exclude_prefixes=("_",),
    )


def _check_file(context: ProjectContext, path: Path, errors: ErrorSink) -> None:
    text = context.read_text(path)
    require_first_nonempty_line(context, path, text, "# %%", errors)
    require_module_docstring(context, path, text, errors)
    require_section_order(
        context,
        path,
        text,
        [
            "Scenario",
            "Pipeline",
            "Demo (Manual Execution)",
            "Expected Output",
        ],
        errors,
    )
    require_top_level_function(context, path, text, "main", errors)
    expect(
        context,
        path,
        "EXPECTED_OUTPUT" in text,
        "missing `EXPECTED_OUTPUT` example block",
        errors,
    )


SPECS = (
    CheckSpec(
        "verification.workbench_script_template",
        _select_paths,
        _check_file,
    ),
)
