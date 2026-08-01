#!/usr/bin/env python3
"""Ternforge-specific Python repository policy retained after the tooling split.

Generic import relationships, formatting, typing, security, dependency, and
packaging checks intentionally stay in Ruff, import-linter, Pyright, pytest,
Bandit, Deptry, uv, and the packaging tools. This module contains only product
rules that those tools do not express directly.
"""

from __future__ import annotations

import argparse
import ast
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

_TOOL_TABLE = "ternforge"
_ANSWERS_FILE = "_copier_answers.yml"
_PACKAGE_PLACEHOLDER = "__PACKAGE_NAME__"
_IGNORED_PARTS = {".git", ".venv", "build", "dist", "__pycache__"}

_REQUIRED_API_FILES = (
    "__init__.py",
    "config.py",
    "defaults.py",
    "errors.py",
    "types.py",
)
_REQUIRED_CONFIG_FILES = (
    "__init__.py",
    "assembly.py",
    "models.py",
    "state.py",
    "validation.py",
)
_REQUIRED_TEST_ROOT_PATHS = ("README.md", "__init__.py")
_REQUIRED_PACKAGE_TEST_PATHS = (
    "__init__.py",
    "conftest.py",
    "e2e/__init__.py",
    "integration/__init__.py",
    "property_based/__init__.py",
    "property_based/internal/__init__.py",
    "property_based/public_contract/__init__.py",
    "support/__init__.py",
    "unit/__init__.py",
)
_REQUIRED_TEMPLATE_TEST_PATHS = (
    "e2e/public_boundary/__init__.py",
    "e2e/public_boundary/test_public_config_pipeline.py",
    "integration/test_config_lifecycle.py",
    "property_based/public_contract/test_config_contract.py",
    "unit/test_public_package.py",
)
_PACKAGE_DOCS = (
    "README.md",
    "architecture/README.md",
    "architecture/concepts/README.md",
    "architecture/concepts/public-boundary-and-errors.md",
    "architecture/flows/README.md",
    "architecture/system.md",
    "dependencies.md",
    "usage.md",
    "verification/README.md",
    "verification/e2e/README.md",
    "verification/public-boundary-and-errors.md",
    "verification/workbench.md",
)


@dataclass(frozen=True, slots=True)
class Violation:
    """One deterministic policy violation."""

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


@dataclass(frozen=True, slots=True)
class ProjectPolicyConfig:
    """Policy-facing Ternforge project metadata."""

    primary_package: str
    package_names: tuple[str, ...]
    public_namespace_packages: tuple[str, ...]


def _table(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _normalize_start(start: Path | None) -> Path:
    return (start or Path.cwd()).expanduser().resolve()


def _find_pyproject(start: Path | None = None) -> Path:
    candidate = _normalize_start(start)
    if candidate.is_file():
        candidate = candidate.parent
    for root in (candidate, *candidate.parents):
        path = root / "pyproject.toml"
        if path.is_file():
            return path
    raise FileNotFoundError(f"Could not find pyproject.toml above {candidate}.")


def _read_toml(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        value = tomllib.load(stream)
    if not isinstance(value, dict):
        raise TypeError("pyproject.toml root must be a table")
    return value


def _string_tuple(value: object, *, field: str, required: bool = False) -> tuple[str, ...]:
    if value is None and not required:
        return ()
    if not isinstance(value, list) or not value:
        raise TypeError(f"[tool.{_TOOL_TABLE}].{field} must be a non-empty string list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"[tool.{_TOOL_TABLE}].{field} items must be non-empty strings")
        result.append(item.strip())
    return tuple(dict.fromkeys(result))


def _project_config(root: Path) -> ProjectPolicyConfig:
    raw = _read_toml(root / "pyproject.toml")
    tooling = _table(_table(raw.get("tool")).get(_TOOL_TABLE))
    if not tooling:
        raise TypeError(f"pyproject.toml must define [tool.{_TOOL_TABLE}]")
    primary = tooling.get("primary_package")
    if not isinstance(primary, str) or not primary.strip():
        raise ValueError(f"[tool.{_TOOL_TABLE}].primary_package must be a non-empty string")
    package_names = _string_tuple(tooling.get("package_names"), field="package_names", required=True)
    primary = primary.strip()
    if primary not in package_names:
        raise ValueError(f"[tool.{_TOOL_TABLE}].primary_package must appear in package_names")
    public_namespaces = _string_tuple(
        tooling.get("public_namespace_packages"),
        field="public_namespace_packages",
    )
    return ProjectPolicyConfig(
        primary_package=primary,
        package_names=package_names,
        public_namespace_packages=public_namespaces,
    )


def discover_project_roots(*, start: Path | None = None) -> tuple[Path, ...]:
    """Return standalone or uv-workspace project roots."""
    pyproject = _find_pyproject(start)
    root = pyproject.parent
    raw = _read_toml(pyproject)
    members = _table(_table(raw.get("tool")).get("uv"))
    workspace = _table(members.get("workspace"))
    values = workspace.get("members")
    if not isinstance(values, list):
        return (root,)
    roots = tuple(
        root / item.strip()
        for item in values
        if isinstance(item, str) and item.strip()
    )
    return roots or (root,)


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


def _iter_python(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.py")):
        if not any(part in _IGNORED_PARTS for part in path.parts):
            yield path


def _has_cell_marker(path: Path) -> bool:
    try:
        return path.read_text(encoding="utf-8").splitlines()[0].strip() == "# %%"
    except (OSError, UnicodeDecodeError, IndexError):
        return False


def _doc_or_future(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ) or (isinstance(node, ast.ImportFrom) and node.module == "__future__")


def _constant_assignment(node: ast.stmt) -> bool:
    targets: list[ast.expr]
    if isinstance(node, ast.Assign):
        targets = list(node.targets)
    elif isinstance(node, ast.AnnAssign):
        targets = [node.target]
    else:
        return False
    return all(isinstance(target, ast.Name) and target.id.isupper() for target in targets)


def _exception_class(node: ast.ClassDef) -> bool:
    for base in node.bases:
        name = base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else ""
        if name.endswith(("Error", "Exception")):
            return True
    return False


def _allowed_root_statement(node: ast.stmt, package: str) -> bool:
    if _doc_or_future(node):
        return True
    if isinstance(node, ast.ImportFrom):
        return node.module == "importlib.metadata" or (
            node.module is not None
            and (node.module == f"{package}._api" or node.module.startswith(f"{package}._api."))
        )
    if isinstance(node, ast.Import):
        return all(alias.name == "importlib.metadata" for alias in node.names)
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return all(
            isinstance(target, ast.Name) and target.id in {"__all__", "__version__"}
            for target in targets
        )
    if isinstance(node, ast.Try):
        nested = [*node.body, *node.orelse, *node.finalbody]
        nested.extend(statement for handler in node.handlers for statement in handler.body)
        return all(_allowed_root_statement(statement, package) for statement in nested)
    return False


def _check_console_scripts(root: Path, config: ProjectPolicyConfig) -> list[Violation]:
    raw = _read_toml(root / "pyproject.toml")
    scripts = _table(_table(raw.get("project")).get("scripts"))
    facade = root / "src" / config.primary_package / "_api" / "cli.py"
    tree = _parse(facade) if facade.is_file() else None
    functions = {
        node.name
        for node in (tree.body if tree else ())
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    }
    violations: list[Violation] = []
    prefix = f"{config.primary_package}._api.cli:"
    for name, target in sorted(scripts.items()):
        if not isinstance(target, str) or not target.startswith(prefix):
            violations.append(Violation(root / "pyproject.toml", f"project scripts must target `{prefix}*`"))
            continue
        function = target.partition(":")[2]
        if tree is None:
            violations.append(Violation(facade, "project scripts require an `_api/cli.py` facade"))
        elif function not in functions:
            violations.append(
                Violation(facade, f"project script `{name}` target function is missing from `_api/cli.py`")
            )
    return violations


def _check_root_initializer(path: Path, package: str) -> list[Violation]:
    tree = _parse(path) if path.is_file() else None
    if tree is None:
        return [Violation(path, "root package __init__.py must exist and parse")]
    return [
        Violation(path, "root __init__.py may contain only declaration/facade imports", node.lineno)
        for node in tree.body
        if not _allowed_root_statement(node, package)
    ]


def _check_declaration_module(path: Path) -> list[Violation]:
    tree = _parse(path)
    if tree is None:
        return [Violation(path, "could not parse `_api` declaration module")]
    violations: list[Violation] = []
    for node in tree.body:
        allowed = _doc_or_future(node)
        if path.name == "__init__.py":
            pass
        elif path.name == "config.py":
            allowed = allowed or isinstance(node, ast.ImportFrom)
        elif path.name == "defaults.py":
            allowed = allowed or isinstance(node, (ast.Import, ast.ImportFrom)) or _constant_assignment(node)
        elif path.name == "errors.py":
            allowed = allowed or isinstance(node, (ast.Import, ast.ImportFrom)) or (
                isinstance(node, ast.ClassDef) and _exception_class(node)
            )
        elif path.name == "types.py":
            allowed = allowed or isinstance(
                node,
                (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.ClassDef, ast.TypeAlias),
            )
        if not allowed:
            messages = {
                "__init__.py": "`_api/__init__.py` must stay empty except docstring/future import",
                "config.py": "`_api/config.py` must contain imports only",
                "defaults.py": "`_api/defaults.py` must contain constants only",
                "errors.py": "`_api/errors.py` must contain public exception classes only",
                "types.py": "`_api/types.py` must contain public type declarations only",
            }
            violations.append(Violation(path, messages[path.name], node.lineno))
    return violations


def _check_product_facade(path: Path) -> list[Violation]:
    tree = _parse(path)
    if tree is None:
        return [Violation(path, "could not parse `_api` module")]
    definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not node.name.startswith("_")
    ]
    return [] if definitions else [Violation(path, "product `_api` modules must define facades, not re-export wrappers")]


def _assigns_all(node: ast.stmt) -> bool:
    if isinstance(node, ast.Assign):
        return any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
    return isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "__all__"


def _check_package(root: Path, package: str, config: ProjectPolicyConfig) -> list[Violation]:
    package_root = root / "src" / package
    required = [
        package_root / "__init__.py",
        package_root / "py.typed",
        package_root / "_api",
        package_root / "_internal",
        package_root / "_internal" / "__init__.py",
    ]
    required.extend(package_root / "_api" / item for item in _REQUIRED_API_FILES)
    required.extend(package_root / "_internal" / "config" / item for item in _REQUIRED_CONFIG_FILES)
    violations = [Violation(path, "required Ternforge package path is missing") for path in required if not path.exists()]
    violations.extend(_check_root_initializer(package_root / "__init__.py", package))

    if package_root.is_dir():
        allowed_dirs = {"_api", "_internal", *config.public_namespace_packages}
        for child in sorted(package_root.iterdir()):
            if child.name == "__pycache__":
                continue
            if child.is_file() and child.name not in {"__init__.py", "py.typed"}:
                violations.append(Violation(child, "public-looking root module must live under `_api` or `_internal`"))
            elif child.is_dir() and child.name not in allowed_dirs:
                violations.append(
                    Violation(child, "public-looking root package must be declared or moved under `_api`/`_internal`")
                )

    internal = package_root / "_internal"
    if internal.is_dir():
        violations.extend(
            Violation(path, "private implementation modules must live in `_internal` subpackages")
            for path in sorted(internal.glob("*.py"))
            if path.name != "__init__.py"
        )

    api_root = package_root / "_api"
    if api_root.is_dir():
        for path in sorted(api_root.glob("*.py")):
            if path.name in _REQUIRED_API_FILES:
                violations.extend(_check_declaration_module(path))
            else:
                violations.extend(_check_product_facade(path))

    root_init = package_root / "__init__.py"
    for path in _iter_python(package_root):
        if path == root_init:
            continue
        tree = _parse(path)
        if tree is None:
            continue
        violations.extend(
            Violation(path, "`__all__` must be declared only in root package", node.lineno)
            for node in tree.body
            if _assigns_all(node)
        )
    return violations


def _check_dynamic_private_imports(root: Path, packages: Iterable[str]) -> list[Violation]:
    prefixes = tuple(f"{package}._internal" for package in packages)
    violations: list[Violation] = []
    for path in _iter_python(root):
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
                violations.append(Violation(path, "string-based dynamic import of `_internal` is forbidden", node.lineno))
    return violations


def _check_examples(root: Path, packages: tuple[str, ...]) -> list[Violation]:
    examples = root / "examples"
    if not examples.exists():
        return []
    if not examples.is_dir():
        return [Violation(examples, "examples must be a directory")]
    meaningful = [child for child in examples.iterdir() if child.name != "__pycache__"]
    if not meaningful:
        return []
    violations: list[Violation] = []
    for child in sorted(meaningful):
        if child.is_file() and child.name == "__init__.py":
            continue
        if child.is_file() or child.name not in set(packages):
            violations.append(Violation(child, "examples must live under `examples/<package>/`"))
    for package in packages:
        package_root = examples / package
        if not package_root.is_dir():
            continue
        for path in sorted(package_root.rglob("*.py")):
            if path.name != "__init__.py" and not _has_cell_marker(path):
                violations.append(Violation(path, "runnable examples must start with `# %%` for IPython console use"))
            tree = _parse(path)
            if tree is None:
                violations.append(Violation(path, "example source must be valid Python"))
                continue
            prefixes = ("src", f"{package}._api", f"{package}._internal")
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if any(node.value == prefix or node.value.startswith(f"{prefix}.") for prefix in prefixes):
                        violations.append(Violation(path, "examples must not reference private package modules", node.lineno))
    return violations


def _check_tests(root: Path, packages: tuple[str, ...]) -> list[Violation]:
    tests = root / "tests"
    required = [tests / item for item in _REQUIRED_TEST_ROOT_PATHS]
    for package in packages:
        package_root = tests / package
        required.extend(package_root / item for item in _REQUIRED_PACKAGE_TEST_PATHS)
        required.extend(package_root / item for item in _REQUIRED_TEMPLATE_TEST_PATHS)
    violations = [Violation(path, "required Ternforge test path is missing") for path in required if not path.exists()]
    for package in packages:
        e2e = tests / package / "e2e"
        if not e2e.is_dir():
            continue
        violations.extend(
            Violation(path, "runnable e2e tests must start with `# %%` for IPython console use")
            for path in sorted(e2e.rglob("*.py"))
            if path.name != "__init__.py" and not _has_cell_marker(path)
        )
    return violations


def _check_workbench(root: Path) -> list[Violation]:
    workbench = root / "workbench"
    if not workbench.exists():
        return []
    if not workbench.is_dir():
        return [Violation(workbench, "workbench must be a directory")]
    return [
        Violation(path, "runnable workbench modules must start with `# %%` for IPython console use")
        for path in sorted(workbench.rglob("*.py"))
        if path.name != "__init__.py" and not _has_cell_marker(path)
    ]


def _load_e2e_slices(root: Path) -> tuple[tuple[str, Path], ...]:
    answers = root / _ANSWERS_FILE
    if not answers.is_file():
        return ()
    value = yaml.safe_load(answers.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{_ANSWERS_FILE} must contain a mapping")
    raw = value.get("e2e_slices", ())
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise TypeError(f"{_ANSWERS_FILE} e2e_slices must be a list")
    result: list[tuple[str, Path]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise TypeError(f"{_ANSWERS_FILE} e2e_slices items must be mappings")
        name = item.get("name")
        path = item.get("path")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{_ANSWERS_FILE} e2e slice name must be a non-empty string")
        if not isinstance(path, str) or not path.strip():
            raise ValueError(f"{_ANSWERS_FILE} e2e slice path must be a non-empty string")
        normalized = Path(path.strip())
        if normalized.is_absolute():
            raise ValueError(f"{_ANSWERS_FILE} e2e slice path must be relative")
        result.append((name.strip(), normalized))
    return tuple(result)


def _check_docs(root: Path, config: ProjectPolicyConfig) -> list[Violation]:
    required = [root / "docs" / "README.md"]
    for package in config.package_names:
        docs = root / "docs" / package
        required.extend(docs / item for item in _PACKAGE_DOCS)
    violations = [Violation(path, "required Ternforge docs file is missing") for path in required if not path.is_file()]
    try:
        slices = _load_e2e_slices(root)
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        return [*violations, Violation(root / _ANSWERS_FILE, str(exc))]
    for name, path in slices:
        resolved = Path(str(path).replace(_PACKAGE_PLACEHOLDER, config.primary_package))
        if not (root / resolved).is_dir():
            violations.append(Violation(root / resolved, "configured e2e slice directory is missing"))
        doc = root / "docs" / config.primary_package / "verification" / "e2e" / f"{name}.md"
        if not doc.is_file():
            violations.append(Violation(doc, "configured e2e slice documentation is missing"))
    return violations


def check_project_root(root: Path) -> tuple[Violation, ...]:
    root = root.resolve()
    try:
        config = _project_config(root)
    except (OSError, TypeError, ValueError, tomllib.TOMLDecodeError) as exc:
        return (Violation(root / "pyproject.toml", str(exc)),)
    violations: list[Violation] = []
    violations.extend(_check_console_scripts(root, config))
    for package in config.package_names:
        violations.extend(_check_package(root, package, config))
    violations.extend(_check_dynamic_private_imports(root, config.package_names))
    violations.extend(_check_examples(root, config.package_names))
    violations.extend(_check_tests(root, config.package_names))
    violations.extend(_check_workbench(root))
    violations.extend(_check_docs(root, config))
    return tuple(sorted(violations, key=lambda item: (str(item.path), item.line or 0, item.message)))


def check(*, start: Path | None = None) -> tuple[Violation, ...]:
    try:
        roots = discover_project_roots(start=start)
    except (OSError, TypeError, ValueError, tomllib.TOMLDecodeError) as exc:
        path = _normalize_start(start) / "pyproject.toml"
        return (Violation(path, str(exc)),)
    violations: list[Violation] = []
    for root in roots:
        violations.extend(check_project_root(root))
    return tuple(sorted(violations, key=lambda item: (str(item.path), item.line or 0, item.message)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.root.resolve()
    violations = check(start=root)
    for violation in violations:
        print(violation.render(root))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
