from __future__ import annotations

import argparse
import ast
import json
import os
import re
import tomllib
from pathlib import Path
from typing import Any

ASSET_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ASSET_ROOT.parents[1]
WORKSPACE_ROOT = REPOSITORY_ROOT.parent
LEGACY = WORKSPACE_ROOT / "py-lib-starter"
NOTES = WORKSPACE_ROOT / "betabit-notes" / "ternforge"
LAB = REPOSITORY_ROOT


def rel(path: Path, base: Path | None = None) -> str:
    return path.relative_to(base or LEGACY).as_posix()


def parse_module(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"path": rel(path), "syntax_error": str(exc)}
    defs: list[dict[str, Any]] = []
    imports: list[dict[str, Any]] = []
    all_names: list[str] | None = None
    constants: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.append(
                {
                    "name": node.name,
                    "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                    "public": not node.name.startswith("_"),
                    "line": node.lineno,
                    "doc": (ast.get_docstring(node) or "").splitlines()[0:1],
                }
            )
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                {
                    "module": node.module,
                    "names": [alias.asname or alias.name for alias in node.names],
                    "raw_names": [alias.name for alias in node.names],
                    "level": node.level,
                }
            )
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constants.append(target.id)
                    if target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        values: list[str] = []
                        for element in node.value.elts:
                            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                                values.append(element.value)
                        all_names = values
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            constants.append(node.target.id)
    return {
        "path": rel(path),
        "module_doc": (ast.get_docstring(tree) or "").splitlines()[0:1],
        "defs": defs,
        "imports": imports,
        "constants": constants,
        "all": all_names,
    }


def pyproject(path: Path) -> dict[str, Any]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    return {
        "path": rel(path),
        "name": project.get("name"),
        "dependencies": project.get("dependencies", []),
        "optional_dependencies": project.get("optional-dependencies", {}),
        "scripts": project.get("scripts", {}),
        "entry_points": project.get("entry-points", {}),
    }


def test_inventory(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sorted(root.rglob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        tests: list[str] = []
        fixtures: list[str] = []
        classes: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    tests.append(node.name)
                for dec in node.decorator_list:
                    name = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                    if "fixture" in name:
                        fixtures.append(node.name)
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                classes.append(node.name)
        out.append({"path": rel(path), "tests": sorted(set(tests)), "fixtures": sorted(set(fixtures)), "classes": classes})
    return out


def shell_inventory() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    roots = [LEGACY / "scripts", LEGACY / ".github"]
    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in {".sh", ".yml", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            out.append(
                {
                    "path": rel(path),
                    "lines": len(text.splitlines()),
                    "commands": sorted(
                        set(
                            re.findall(
                                r"\b(?:py-lib-[a-z0-9-]+|uv|copier|gh|git|docker|direnv|pre-commit|pytest|ruff|pyright|ty|bandit|gitleaks|renovate|release-please)\b",
                                text,
                            )
                        )
                    ),
                    "functions": re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)\(\)\s*\{", text, flags=re.MULTILINE),
                }
            )
    return out


def template_inventory() -> dict[str, Any]:
    builds: dict[str, Any] = {}
    for build in sorted((LEGACY / "template-builds").iterdir()):
        if not build.is_dir():
            continue
        files = [p.relative_to(build).as_posix() for p in sorted(build.rglob("*")) if p.is_file()]
        builds[build.name] = {
            "file_count": len(files),
            "files": files,
            "top_levels": sorted({f.split("/", 1)[0] for f in files}),
        }
    manifests: dict[str, Any] = {}
    for manifest in sorted((LEGACY / "template-manifests").glob("*/manifest.yml")):
        manifests[manifest.parent.name] = manifest.read_text(encoding="utf-8")
    components: dict[str, Any] = {}
    for comp in sorted((LEGACY / "template-components").iterdir()):
        if comp.is_dir():
            files = [p.relative_to(comp).as_posix() for p in sorted(comp.rglob("*")) if p.is_file()]
            components[comp.name] = {"file_count": len(files), "files": files}
    return {"builds": builds, "manifests": manifests, "component_groups": components}


def docs_inventory() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sorted(LEGACY.rglob("*.md")):
        if "/.venv/" in path.as_posix() or "/.git/" in path.as_posix():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        headings = re.findall(r"^(#{1,4})\s+(.+)$", text, flags=re.MULTILINE)
        out.append({"path": rel(path), "headings": [title for _, title in headings], "lines": len(text.splitlines())})
    return out


def record_mentions() -> dict[str, list[str]]:
    terms = [
        "python-internal-package",
        "python-starter-platform",
        "portability",
        "setup",
        "doctor",
        "onboarding",
        "public import",
        "public API",
        "configuration",
        "logging",
        "cache",
        "previews",
        "validation",
        "fixture",
        "agent",
        "testkit",
        "runtime",
        "policy",
        "project-info",
        "running-loop",
    ]
    result: dict[str, list[str]] = {term: [] for term in terms}
    for path in sorted(NOTES.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for term in terms:
            if term.lower() in text:
                result[term].append(path.relative_to(NOTES).as_posix())
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inventory the frozen legacy Ternforge product surface.")
    parser.add_argument("--workspace", type=Path, default=WORKSPACE_ROOT)
    parser.add_argument("--legacy", type=Path)
    parser.add_argument("--notes", type=Path)
    parser.add_argument("--lab", type=Path)
    parser.add_argument("--output", type=Path, default=ASSET_ROOT / "legacy-inventory.json")
    return parser


def main(argv: list[str] | None = None) -> None:
    global LAB, LEGACY, NOTES

    args = _parser().parse_args(argv)
    workspace = args.workspace.resolve()
    LEGACY = (args.legacy or workspace / "py-lib-starter").resolve()
    NOTES = (args.notes or workspace / "betabit-notes" / "ternforge").resolve()
    LAB = (args.lab or REPOSITORY_ROOT).resolve()
    out = args.output.resolve()

    required = {
        "legacy repository": LEGACY,
        "Ternforge notes": NOTES,
        "lab-control repository": LAB,
    }
    missing = [f"{label}: {path}" for label, path in required.items() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing inventory inputs:\n" + "\n".join(missing))

    source_roots = [LEGACY / "src", LEGACY / "packages/py-lib-runtime/src", LEGACY / "packages/py-lib-tooling/src"]
    modules = [parse_module(path) for root in source_roots for path in sorted(root.rglob("*.py"))]
    projects = [
        pyproject(LEGACY / "pyproject.toml"),
        pyproject(LEGACY / "packages/py-lib-runtime/pyproject.toml"),
        pyproject(LEGACY / "packages/py-lib-tooling/pyproject.toml"),
    ]
    tests = []
    for root in [LEGACY / "tests", LEGACY / "packages/py-lib-runtime/tests", LEGACY / "packages/py-lib-tooling/tests"]:
        tests.extend(test_inventory(root))
    payload = {
        "revisions": {
            "betabit_notes": os.popen(f"git -C '{NOTES.parent}' rev-parse HEAD").read().strip(),
            "py_lib_starter": os.popen(f"git -C '{LEGACY}' rev-parse HEAD").read().strip(),
            "lab_control": os.popen(f"git -C '{LAB}' rev-parse HEAD").read().strip(),
        },
        "projects": projects,
        "modules": modules,
        "tests": tests,
        "shell_and_workflows": shell_inventory(),
        "templates": template_inventory(),
        "docs": docs_inventory(),
        "record_mentions": record_mentions(),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "projects": len(projects),
        "modules": len(modules),
        "test_files": len(tests),
        "test_cases": sum(len(x["tests"]) for x in tests),
        "shell_and_workflows": len(payload["shell_and_workflows"]),
        "docs": len(payload["docs"]),
        "template_builds": {k: v["file_count"] for k, v in payload["templates"]["builds"].items()},
        "output": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()
