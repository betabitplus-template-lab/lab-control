"""Shared Python source parsing and validation helpers."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from _shared.context import ErrorSink, ProjectContext
from _shared.reporting import expect


def module_docstring(text: str) -> str | None:
    """Return the module docstring when the file parses cleanly."""
    return ast.get_docstring(ast.parse(text), clean=False)


def docstring_labels(docstring: str) -> list[str]:
    """Extract colon-terminated section labels from one docstring."""
    return re.findall(r"^([A-Z][A-Za-z ]+):$", docstring, flags=re.MULTILINE)


def section_titles(text: str) -> list[str]:
    """Extract three-line section-banner titles from a Python file."""
    titles: list[str] = []
    lines = text.splitlines()
    for index in range(len(lines) - 2):
        if not re.fullmatch(r"\s*# =+\s*", lines[index]):
            continue
        title_match = re.fullmatch(r"\s*# (.+?)\s*", lines[index + 1])
        if title_match is None:
            continue
        if not re.fullmatch(r"\s*# =+\s*", lines[index + 2]):
            continue
        titles.append(title_match.group(1))
    return titles


def top_level_function_names(text: str) -> list[str]:
    """Return top-level function names from a Python module."""
    return [
        node.name
        for node in ast.parse(text).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def first_nonempty_line(text: str) -> str:
    """Return the first non-empty source line."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def require_module_docstring(
    context: ProjectContext,
    path: Path,
    text: str,
    errors: ErrorSink,
) -> str | None:
    """Require a parseable module docstring and return it."""
    try:
        docstring = module_docstring(text)
    except SyntaxError as error:
        errors.append(
            f"{context.display_path(path)}: could not parse Python file: {error.msg}"
        )
        return None

    expect(
        context,
        path,
        docstring is not None,
        "missing module docstring",
        errors,
    )
    if docstring is not None:
        expect(
            context,
            path,
            bool(first_nonempty_line(docstring)),
            "module docstring should start with a short summary line",
            errors,
        )
    return docstring


def require_docstring_label_order(
    context: ProjectContext,
    path: Path,
    docstring: str,
    expected: list[str],
    errors: ErrorSink,
) -> None:
    """Require present docstring labels to appear in the expected order."""
    labels = docstring_labels(docstring)
    positions = {label: expected.index(label) for label in labels if label in expected}
    actual = [label for label in labels if label in positions]
    sorted_actual = sorted(actual, key=positions.__getitem__)
    expect(
        context,
        path,
        actual == sorted_actual,
        "docstring section labels are out of order",
        errors,
    )


def require_docstring_labels(
    context: ProjectContext,
    path: Path,
    docstring: str,
    required: list[str],
    errors: ErrorSink,
) -> None:
    """Require specific labels to appear in one docstring."""
    labels = set(docstring_labels(docstring))
    for label in required:
        expect(
            context,
            path,
            label in labels,
            f"docstring should include `{label}:`",
            errors,
        )


def require_section_order(
    context: ProjectContext,
    path: Path,
    text: str,
    required: list[str],
    errors: ErrorSink,
) -> None:
    """Require section-banner titles to appear in the expected order."""
    titles = section_titles(text)
    last_index = -1
    for title in required:
        expect(context, path, title in titles, f"missing `{title}` section", errors)
        if title not in titles:
            continue
        current_index = titles.index(title)
        expect(
            context,
            path,
            current_index > last_index,
            f"`{title}` is out of order",
            errors,
        )
        last_index = current_index


def require_first_nonempty_line(
    context: ProjectContext,
    path: Path,
    text: str,
    expected: str,
    errors: ErrorSink,
) -> None:
    """Require one exact first non-empty line."""
    expect(
        context,
        path,
        first_nonempty_line(text) == expected,
        f"first non-empty line should be `{expected}`",
        errors,
    )


def require_top_level_function(
    context: ProjectContext,
    path: Path,
    text: str,
    function_name: str,
    errors: ErrorSink,
) -> None:
    """Require one named top-level function."""
    try:
        function_names = top_level_function_names(text)
    except SyntaxError as error:
        errors.append(
            f"{context.display_path(path)}: could not parse Python file: {error.msg}"
        )
        return
    expect(
        context,
        path,
        function_name in function_names,
        f"missing top-level `{function_name}()`",
        errors,
    )
