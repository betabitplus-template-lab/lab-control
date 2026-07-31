"""Checks for Python file docstrings shaped by core/docstring_template.md."""

from __future__ import annotations

from pathlib import Path

from _shared.context import CheckSpec, ErrorSink, ProjectContext
from _shared.python_source import (
    require_docstring_label_order,
    require_docstring_labels,
    require_module_docstring,
)

_REGULAR_LABELS = ["Why", "When to use", "How", "Notes", "Examples"]
_PACKAGE_LABELS = [
    "Why",
    "What belongs here",
    "What does not belong here",
    "Examples",
]
_SCENARIO_LABELS = ["Why", "Covers", "Checks", "Notes", "Examples"]


def _select_regular_modules(context: ProjectContext) -> list[Path]:
    return context.src_glob("**/*.py", exclude_names=("__init__.py",))


def _check_regular_module(
    context: ProjectContext,
    path: Path,
    errors: ErrorSink,
) -> None:
    docstring = require_module_docstring(context, path, context.read_text(path), errors)
    if docstring is None:
        return
    require_docstring_label_order(context, path, docstring, _REGULAR_LABELS, errors)


def _select_package_modules(context: ProjectContext) -> list[Path]:
    return context.src_glob("**/__init__.py")


def _check_package_module(
    context: ProjectContext,
    path: Path,
    errors: ErrorSink,
) -> None:
    docstring = require_module_docstring(context, path, context.read_text(path), errors)
    if docstring is None:
        return
    require_docstring_labels(context, path, docstring, ["Why"], errors)
    require_docstring_label_order(context, path, docstring, _PACKAGE_LABELS, errors)


def _select_e2e_docstrings(context: ProjectContext) -> list[Path]:
    return context.tests_glob("**/e2e/**/test_*.py")


def _check_e2e_docstring(
    context: ProjectContext,
    path: Path,
    errors: ErrorSink,
) -> None:
    docstring = require_module_docstring(context, path, context.read_text(path), errors)
    if docstring is None:
        return
    require_docstring_labels(
        context,
        path,
        docstring,
        ["Why", "Covers", "Checks", "Examples"],
        errors,
    )
    require_docstring_label_order(context, path, docstring, _SCENARIO_LABELS, errors)


def _select_workbench_docstrings(context: ProjectContext) -> list[Path]:
    return context.workbench_glob(
        "**/*.py",
        exclude_names=("__init__.py",),
        exclude_prefixes=("_",),
    )


def _check_workbench_docstring(
    context: ProjectContext,
    path: Path,
    errors: ErrorSink,
) -> None:
    docstring = require_module_docstring(context, path, context.read_text(path), errors)
    if docstring is None:
        return
    require_docstring_labels(
        context,
        path,
        docstring,
        ["Why", "Covers", "Checks", "Examples"],
        errors,
    )
    require_docstring_label_order(context, path, docstring, _SCENARIO_LABELS, errors)


SPECS = (
    CheckSpec(
        "core.docstring_template.regular",
        _select_regular_modules,
        _check_regular_module,
    ),
    CheckSpec(
        "core.docstring_template.package",
        _select_package_modules,
        _check_package_module,
    ),
    CheckSpec(
        "core.docstring_template.e2e",
        _select_e2e_docstrings,
        _check_e2e_docstring,
    ),
    CheckSpec(
        "core.docstring_template.workbench",
        _select_workbench_docstrings,
        _check_workbench_docstring,
    ),
)
