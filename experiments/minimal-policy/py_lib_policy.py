#!/usr/bin/env python3
"""Minimal organization-specific Python architecture policy checker.

This checker intentionally contains no template, update, GitHub, registry, release,
or runtime configuration logic. Generic import relationships belong in
import-linter/Ruff/Pyright; this script covers only conventions those tools do
not express directly.
"""
from __future__ import annotations

import argparse
import ast
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DOCS_SKELETON = (
    "README.md",
    "architecture/README.md",
    "architecture/system.md",
    "dependencies.md",
    "usage.md",
    "verification/README.md",
)


@dataclass(frozen=True)
class Violation:
    path: Path
    message: str
    line: int | None = None

    def render(self, root: Path) -> str:
        try:
            display = self.path.relative_to(root)
        except ValueError:
            display = self.path
        suffix = f":{self.line}" if self.line else ""
        return f"{display}{suffix}: {self.message}"


def _table(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _load_pyproject(root: Path) -> dict[str, object]:
    path = root / "pyproject.toml"
    if not path.is_file():
        raise ValueError("project root must contain pyproject.toml")
    with path.open("rb") as stream:
        value = tomllib.load(stream)
    if not isinstance(value, dict):
        raise ValueError("pyproject.toml root must be a table")
    return value


def _package_names(pyproject: dict[str, object]) -> tuple[str, ...]:
    tool = _table(pyproject.get("tool"))
    starter = _table(tool.get("py_lib_starter"))
    names = starter.get("package_names")
    if isinstance(names, list) and all(isinstance(x, str) and x for x in names):
        return tuple(names)
    project = _table(pyproject.get("project"))
    name = project.get("name")
    if isinstance(name, str) and name:
        return (name.replace("-", "_"),)
    raise ValueError("cannot infer package names")


def _primary_package(pyproject: dict[str, object], names: tuple[str, ...]) -> str:
    starter = _table(_table(pyproject.get("tool")).get("py_lib_starter"))
    value = starter.get("primary_package")
    return value if isinstance(value, str) and value else names[0]


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


def check_console_scripts(root: Path, pyproject: dict[str, object], primary: str) -> list[Violation]:
    scripts = _table(_table(pyproject.get("project")).get("scripts"))
    cli_path = root / "src" / primary / "_api" / "cli.py"
    tree = _parse(cli_path) if cli_path.is_file() else None
    declared = {
        node.name
        for node in (tree.body if tree else ())
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    }
    out: list[Violation] = []
    for name, target in sorted(scripts.items()):
        expected_prefix = f"{primary}._api.cli:"
        if not isinstance(target, str) or not target.startswith(expected_prefix):
            out.append(Violation(root / "pyproject.toml", f"script {name!r} must target {expected_prefix}*"))
            continue
        function = target.partition(":")[2]
        if not cli_path.is_file():
            out.append(Violation(cli_path, "console scripts require an _api/cli.py facade"))
        elif function not in declared:
            out.append(Violation(cli_path, f"script {name!r} targets missing function {function!r}"))
    return out


def _allowed_root_statement(node: ast.stmt, package: str) -> bool:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        return True
    if isinstance(node, ast.ImportFrom):
        return node.module == "__future__" or node.module == f"{package}._api" or (
            node.module is not None and node.module.startswith(f"{package}._api.")
        ) or node.module == "importlib.metadata"
    if isinstance(node, ast.Import):
        return all(alias.name == "importlib.metadata" for alias in node.names)
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return all(isinstance(target, ast.Name) and target.id in {"__all__", "__version__"} for target in targets)
    if isinstance(node, ast.Try):
        statements = [*node.body, *node.orelse, *node.finalbody]
        statements.extend(statement for handler in node.handlers for statement in handler.body)
        return all(_allowed_root_statement(statement, package) for statement in statements)
    return False


def check_root_initializers(root: Path, packages: Iterable[str]) -> list[Violation]:
    out: list[Violation] = []
    for package in packages:
        path = root / "src" / package / "__init__.py"
        tree = _parse(path) if path.is_file() else None
        if tree is None:
            out.append(Violation(path, "root package __init__.py must exist and parse"))
            continue
        for node in tree.body:
            if not _allowed_root_statement(node, package):
                out.append(Violation(path, "root __init__.py may contain only declaration/facade imports", getattr(node, "lineno", None)))
    return out


def check_dynamic_private_imports(root: Path, packages: Iterable[str]) -> list[Violation]:
    prefixes = tuple(f"{name}._internal" for name in packages)
    out: list[Violation] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in {".venv", ".git", "template-builds"} for part in path.parts):
            continue
        tree = _parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            called = ""
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                called = f"{node.func.value.id}.{node.func.attr}"
            if called not in {"__import__", "importlib.import_module"}:
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str) and first.value.startswith(prefixes):
                out.append(Violation(path, "string-based dynamic import of _internal is forbidden", node.lineno))
    return out


def check_examples(root: Path) -> list[Violation]:
    out: list[Violation] = []
    examples = root / "examples"
    if not examples.exists():
        return out
    for path in sorted(examples.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            first = path.read_text(encoding="utf-8").splitlines()[0].strip()
        except (OSError, UnicodeDecodeError, IndexError):
            first = ""
        if first != "# %%":
            out.append(Violation(path, "Python examples must begin with '# %%'"))
    return out


def check_skeleton(root: Path, packages: Iterable[str]) -> list[Violation]:
    out: list[Violation] = []
    for package in packages:
        required = (
            root / "src" / package / "_api",
            root / "src" / package / "_internal",
            root / "src" / package / "py.typed",
            root / "tests",
        )
        for path in required:
            if not path.exists():
                out.append(Violation(path, "required project skeleton path is missing"))
        docs = root / "docs" / package
        for relative in DOCS_SKELETON:
            path = docs / relative
            if not path.is_file():
                out.append(Violation(path, "required docs skeleton file is missing"))
    return out


def check(root: Path) -> tuple[Violation, ...]:
    root = root.resolve()
    try:
        pyproject = _load_pyproject(root)
        packages = _package_names(pyproject)
        primary = _primary_package(pyproject, packages)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        return (Violation(root / "pyproject.toml", str(exc)),)
    violations: list[Violation] = []
    violations.extend(check_console_scripts(root, pyproject, primary))
    violations.extend(check_root_initializers(root, packages))
    violations.extend(check_dynamic_private_imports(root, packages))
    violations.extend(check_examples(root))
    violations.extend(check_skeleton(root, packages))
    return tuple(sorted(violations, key=lambda item: (str(item.path), item.line or 0, item.message)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    violations = check(args.root)
    for violation in violations:
        print(violation.render(args.root.resolve()))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
