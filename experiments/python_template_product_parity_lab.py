#!/usr/bin/env python3
"""Render and validate a full Python-library product against the frozen starter.

The experiment intentionally treats the generated library as the product. It
keeps that product intact and changes only platform-owned CI, release, update,
and wrapper wiring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml

BASELINE_SHA = "d59582375855cff69fb165e467dc5847bc75ca99"
COPIER_VERSION = "9.16.0"
UV_VERSION = "0.12.0"
RUNTIME_COMMIT = "a4fa84809aa9c5aced3c0a367b23fbcc7f5466d0"
POLICY_COMMIT = "d44737a0887c6bf5d8702d03221845c62e0fed4b"
TESTKIT_COMMIT = "233ebec6a1106fd1b65b84803019494522338667"

PLATFORM_REMOVED_PATHS = {
    ".devcontainer/Dockerfile.ci",
    ".github/actions/setup-dev-env/action.yml",
    ".github/scripts/install-sync-validation-tools.sh",
    ".github/workflows/build-ci-image.yml",
    ".github/workflows/python-lib-ci-baseline.yml",
    ".github/workflows/python-lib-ci-e2e-slice.yml",
    ".github/workflows/python-lib-ci-package.yml",
    ".github/workflows/sync-starter-template.yml",
}

PLATFORM_REPLACED_PATHS = {
    ".github/MAINTAINER_SETUP.md",
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
    "renovate.json5",
}

PRODUCT_ADDED_PATHS = {
    "scripts/reproduce_running_loop.py",
}

PLATFORM_ONLY_HOOKS = {
    "check-branch-name",
    "no-push-to-main",
    "py-lib-check-legacy-support-cleanup",
    "py-lib-template-check",
}

DIRECT_REPLACED_HOOKS = {
    "public-contract-boundary",
    "radon-cc",
    "radon-mi",
    "py-lib-check-cognitive-complexity",
    "py-lib-check-class-attributes-order",
    "py-lib-audit-runtime-dependencies",
    "py-lib-check-project-docs-structure",
    "py-lib-check-project-structure",
}

REQUIRED_PRODUCT_PATHS = {
    ".agents/skills/python-library-rules/SKILL.md",
    ".agents/skills/code-guardrails/SKILL.md",
    ".devcontainer/devcontainer.json",
    ".devcontainer/Dockerfile",
    ".vscode/extensions.json",
    ".vscode/settings.json",
    ".editorconfig",
    ".envrc",
    ".gitleaks.toml",
    ".markdown-link-check.json",
    ".markdownlint.yaml",
    ".mdformat.toml",
    ".pre-commit-config.yaml",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "MANIFEST.in",
    "README.md",
    "RTK.md",
    "SETUP.md",
    "docs/sample_lib/architecture/system.md",
    "docs/sample_lib/dependencies.md",
    "docs/sample_lib/usage.md",
    "examples/sample_lib/config_demo.py",
    "scripts/env/doctor.sh",
    "scripts/env/project_config.sh",
    "scripts/env/secrets.sh",
    "scripts/env/setup.sh",
    "scripts/reproduce_running_loop.py",
    "src/sample_lib/_api/config.py",
    "src/sample_lib/_internal/config/state.py",
    "src/sample_lib/py.typed",
    "tests/sample_lib/e2e/public_boundary/test_public_config_pipeline.py",
    "tests/sample_lib/integration/test_config_lifecycle.py",
    "tests/sample_lib/property_based/public_contract/test_config_contract.py",
    "tests/sample_lib/unit/test_public_package.py",
    "workbench/sample_lib/__init__.py",
}

REQUIRED_TOOL_CONFIGS = {
    "bandit",
    "check-manifest",
    "commitizen",
    "coverage",
    "deptry",
    "importlinter",
    "interrogate",
    "pip-audit",
    "pyright",
    "pytest",
    "ruff",
    "ty",
}

FORBIDDEN_LEGACY_MARKERS = {
    "py-lib-assemble-template",
    "py-lib-check-platform-profile",
    "py-lib-check-starter-packages",
    "py-lib-check-template-components",
    "py-lib-create-managed-repository",
    "py-lib-platform-health-report",
    "py-lib-platform-registry",
    "py-lib-project-info",
    "py-lib-refresh-shared-lock",
    "py-lib-reproduce-running-loop",
    "py-lib-check-legacy-support-cleanup",
    "py-lib-smoke-built-artifacts",
    "py-lib-smoke-installed-artifact",
    "py-lib-smoke-public-api",
    "py-lib-template-answer",
    "py-lib-template-check",
    "py-lib-template-update",
    "py_lib_starter",
    "py_lib_tooling",
    "py-lib-starter",
    "py-lib-tooling",
}

CI_WORKFLOW = """name: CI

on:
  pull_request:
    branches: [main]
    types: [opened, reopened, synchronize, edited]
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: read

jobs:
  ci:
    name: ci
    uses: betabitplus/ternforge-infra-ci/.github/workflows/python-library.yml@1111111111111111111111111111111111111111 # lab contract placeholder
"""

RELEASE_WORKFLOW = """name: Release

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  release:
    uses: betabitplus/ternforge-infra-ci/.github/workflows/release.yml@1111111111111111111111111111111111111111 # lab contract placeholder
    with:
      release-type: python
    secrets: inherit
"""

RENOVATE_CONFIG = """{
  extends: [
    \"github>betabitplus/ternforge-infra-updates//presets/python-library.json5#v0.1.0\",
  ],
}
"""

MAINTAINER_SETUP = """# Maintainer setup

Repository rules, required checks, release credentials, and update automation are
provisioned by Ternforge. Product development remains local to this repository:

```bash
bash scripts/env/setup.sh
bash scripts/env/doctor.sh
```
"""

RUNNING_LOOP_HELPER = '''#!/usr/bin/env python3
"""Run a module while an asyncio event loop is active."""

from __future__ import annotations

import argparse
import asyncio
import runpy
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module")
    parser.add_argument("module_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    for path in (root, root / "src"):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)

    original_argv = sys.argv[:]
    sys.argv = [args.module, *args.module_args]

    async def execute() -> None:
        runpy.run_module(args.module, run_name="__main__")

    try:
        asyncio.run(execute())
    finally:
        sys.argv = original_argv
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def run(
    name: str,
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> CommandResult:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    process = subprocess.run(
        list(command),
        cwd=cwd,
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = CommandResult(
        name=name,
        command=tuple(command),
        returncode=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
    )
    if check and not result.passed:
        rendered = " ".join(command)
        raise RuntimeError(
            f"{name} failed ({process.returncode}): {rendered}\n"
            f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_map(root: Path, *, include_lock: bool = False) -> dict[str, Path]:
    ignored_parts = {
        ".git",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        ".hypothesis",
        ".import_linter_cache",
        "__pycache__",
        "dist",
        "build",
    }
    result: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in ignored_parts for part in relative.parts):
            continue
        if not include_lock and relative.as_posix() == "uv.lock":
            continue
        result[relative.as_posix()] = path
    return result


def remove_hook(text: str, hook_id: str) -> str:
    pattern = re.compile(
        rf"(?ms)^      - id: {re.escape(hook_id)}\n.*?(?=^      - id: |^  - repo: |^  # =|\Z)"
    )
    updated, count = pattern.subn("", text)
    if count != 1:
        raise RuntimeError(f"expected one hook block for {hook_id}, found {count}")
    return updated


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one {label} occurrence, found {count}")
    return text.replace(old, new, 1)


def rewrite_pyproject(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    runtime_old = (
        '  "py-lib-runtime @ git+https://github.com/betabitplus/py-lib-starter.git@v0.32.4'
        '#subdirectory=packages/py-lib-runtime",'
    )
    runtime_new = (
        '  "py-lib-runtime @ git+https://github.com/betabitplus-template-lab/'
        f'sandbox-ternforge-tooling-py-runtime-20260717-r2.git@{RUNTIME_COMMIT}",'
    )
    tooling_old = (
        '  "py-lib-tooling @ git+https://github.com/betabitplus/py-lib-starter.git@v0.32.4'
        '#subdirectory=packages/py-lib-tooling",'
    )
    tooling_new = "\n".join(
        [
            '  "py-lib-policy @ git+https://github.com/betabitplus-template-lab/'
            f'sandbox-ternforge-tooling-py-policy-20260717-r2.git@{POLICY_COMMIT}",',
            '  "py-lib-testkit @ git+https://github.com/betabitplus-template-lab/'
            f'sandbox-ternforge-tooling-py-testkit-20260717-r2.git@{TESTKIT_COMMIT}",',
        ]
    )
    text = replace_once(text, runtime_old, runtime_new, label="runtime dependency")
    text = replace_once(text, tooling_old, tooling_new, label="tooling dependency")
    text = replace_once(text, "[tool.py_lib_starter]", "[tool.ternforge]", label="tool table")
    text = text.replace("# ---------------- Shared py-lib tooling manifest ----------------", "# ---------------- Ternforge project manifest ----------------")
    path.write_text(text, encoding="utf-8")


def rewrite_precommit(path: Path) -> tuple[set[str], set[str]]:
    text = path.read_text(encoding="utf-8")
    baseline_hooks = set(re.findall(r"(?m)^\s+- id: ([^\s]+)", text))
    for hook_id in sorted(PLATFORM_ONLY_HOOKS):
        text = remove_hook(text, hook_id)

    replacements = {
        "entry: uv run py-lib-check-public-contract-boundary": (
            "entry: env PYTHONPATH=src:. uv run lint-imports --config pyproject.toml"
        ),
        "entry: uv run py-lib-check-radon-cc": (
            "entry: >-\n"
            "          bash -c 'output=\"$(uv run radon cc --min C --show-complexity src)\";\n"
            "          printf \"%s\\n\" \"$output\"; test -z \"$output\"'"
        ),
        "entry: uv run py-lib-check-radon-mi": (
            "entry: >-\n"
            "          bash -c 'output=\"$(uv run radon mi --min B --show src)\";\n"
            "          printf \"%s\\n\" \"$output\"; test -z \"$output\"'"
        ),
        "entry: uv run py-lib-check-cognitive-complexity": (
            "entry: uv run flake8 --select=CCR001 --max-cognitive-complexity=15 src"
        ),
        "entry: uv run py-lib-check-class-attributes-order": (
            "entry: >-\n"
            "          uv run flake8 --select=CCE001\n"
            "          --class-attributes-order=field,nested_class,magic_method,property_method,static_method,class_method,method\n"
            "          src"
        ),
        "entry: uv run py-lib-audit-runtime-dependencies": (
            "entry: >-\n"
            "          bash -c 'tmp=\"$(mktemp)\"; trap \"rm -f $tmp\" EXIT;\n"
            "          uv export --frozen --no-dev --no-emit-project --no-emit-package py-lib-runtime --output-file \"$tmp\";\n"
            "          uv run --frozen --no-sync pip-audit --requirement \"$tmp\" --no-deps --disable-pip'"
        ),
        "entry: uv run py-lib-check-project-docs-structure": "entry: uv run py-lib-policy .",
        "entry: uv run py-lib-check-project-structure --strict-template": "entry: uv run py-lib-policy .",
    }
    for old, new in replacements.items():
        text = replace_once(text, old, new, label=old)

    path.write_text(text, encoding="utf-8")
    candidate_hooks = set(re.findall(r"(?m)^\s+- id: ([^\s]+)", text))
    return baseline_hooks, candidate_hooks


def rewrite_project_config(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace('pyproject["tool"]["py_lib_starter"]', 'pyproject["tool"]["ternforge"]')
    text = text.replace("[tool.py_lib_starter].env_prefix", "[tool.ternforge].env_prefix")
    path.write_text(text, encoding="utf-8")


def rewrite_answers(path: Path) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Copier answers must be a mapping")
    for key in (
        "ci_image_copy_paths",
        "runtime_git_ref",
        "runtime_git_subdirectory",
        "runtime_git_url",
        "tooling_git_ref",
        "tooling_git_subdirectory",
        "tooling_git_url",
    ):
        data.pop(key, None)
    data["_src_path"] = "https://github.com/betabitplus/ternforge-template-py-library.git"
    data["_commit"] = "v0.1.0-lab"
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def rewrite_product_namespaces(root: Path) -> set[str]:
    changed: set[str] = set()
    replacements = (
        ("uv run py-lib-smoke-public-api", "uv run pytest tests/sample_lib/e2e/public_boundary -q --no-cov"),
        ("uv run py-lib-smoke-installed-artifact", "uv build"),
        ("uv run py-lib-smoke-built-artifacts", "uv build"),
        ("uv run py-lib-template-check", "uvx --from copier==9.16.0 copier check-update"),
        ("uv run py-lib-template-update", "uvx --from copier==9.16.0 copier update"),
        ("uv run py-lib-reproduce-running-loop", "uv run python scripts/reproduce_running_loop.py"),
        ("uv run py-lib-check-legacy-support-cleanup", "uv run py-lib-policy ."),
        ("uv run py-lib-check-project-docs-structure", "uv run py-lib-policy ."),
        ("shared starter template", "released Ternforge template"),
        ("latest starter template release, normalize shared package refs to one\nversion tag, and refresh shared package lock entries", "latest released Ternforge template"),
        ("normal `dev` to `main`\nPR flow", "normal pull request to `main`"),
        ("For an aggregated `dev` to `main` pull request", "For every pull request to `main`"),
        ("Full CI runs on `dev` pushes and on pull requests targeting `dev` or\n`main`. Pull requests targeting `main` must come from the same repository's\n`dev` branch. `main` pushes run Release only.", "Full CI runs on every pull request targeting `main`. Merges to `main` run the release workflow."),
        ("Check and apply starter template and shared package updates through the shared\ncommands", "Check and apply released Ternforge template updates with Copier"),
        ("Run cleanup, structural, and artifact checks directly when needed", "Run structural and artifact checks directly when needed"),
        ("starter-shaped py-lib repos", "Ternforge-managed Python libraries"),
        ("      # Enforce Git Flow naming conventions (feature/, fix/, etc.)\n", ""),
        ("py_lib_tooling", "py_lib_testkit"),
        ("py-lib-tooling", "py-lib-testkit"),
        ("py_lib_starter", "ternforge"),
        ("py-lib-starter", "Ternforge"),
        ("[tool.py_lib_starter]", "[tool.ternforge]"),
        ("tool.py_lib_starter", "tool.ternforge"),
    )
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.add(path.relative_to(root).as_posix())
    return changed


def normalize_known_baseline_formatting(root: Path) -> set[str]:
    """Apply the one formatting fix required by the frozen template's own Ruff pin."""
    relative = "src/sample_lib/_internal/config/state.py"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    old = """        msg = (\n            \"install_config() expects a \"\n            f\"{SampleLibConfig.__name__} instance.\"\n        )"""
    new = """        msg = f\"install_config() expects a {SampleLibConfig.__name__} instance.\""""
    if old not in text:
        raise RuntimeError("expected frozen formatting fixture was not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return {relative}


def write_product_helpers(root: Path) -> None:
    path = root / "scripts/reproduce_running_loop.py"
    path.write_text(RUNNING_LOOP_HELPER, encoding="utf-8")
    path.chmod(0o755)


def write_platform_files(root: Path) -> None:
    files = {
        ".github/MAINTAINER_SETUP.md": MAINTAINER_SETUP,
        ".github/workflows/ci.yml": CI_WORKFLOW,
        ".github/workflows/release.yml": RELEASE_WORKFLOW,
        "renovate.json5": RENOVATE_CONFIG,
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def render_baseline(baseline_root: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    command = [
        "copier",
        "copy",
        str(baseline_root),
        str(destination),
        "--defaults",
        "--trust",
        "--data",
        "template_profile=python-lib-standard",
    ]
    run("render frozen python-lib-standard", command, cwd=baseline_root)


def transform_candidate(baseline_render: Path, candidate: Path) -> tuple[set[str], set[str], set[str]]:
    if candidate.exists():
        shutil.rmtree(candidate)
    shutil.copytree(baseline_render, candidate, symlinks=True)

    for relative in PLATFORM_REMOVED_PATHS:
        path = candidate / relative
        if not path.exists():
            raise RuntimeError(f"expected platform-owned path is absent: {relative}")
        path.unlink()

    rewrite_pyproject(candidate / "pyproject.toml")
    baseline_hooks, candidate_hooks = rewrite_precommit(candidate / ".pre-commit-config.yaml")
    rewrite_project_config(candidate / "scripts/env/project_config.sh")
    rewrite_answers(candidate / "_copier_answers.yml")
    namespace_changed = rewrite_product_namespaces(candidate)
    formatting_changed = normalize_known_baseline_formatting(candidate)
    write_product_helpers(candidate)
    write_platform_files(candidate)

    for path in sorted(candidate.rglob("*.sh")):
        if path.is_file():
            path.chmod(path.stat().st_mode | 0o111)

    changed = namespace_changed | formatting_changed | PLATFORM_REPLACED_PATHS | {
        ".pre-commit-config.yaml",
        "_copier_answers.yml",
        "pyproject.toml",
        "scripts/env/project_config.sh",
    }
    return baseline_hooks, candidate_hooks, changed


def verify_static_parity(
    baseline: Path,
    candidate: Path,
    *,
    baseline_hooks: set[str],
    candidate_hooks: set[str],
    declared_changed: set[str],
) -> dict[str, object]:
    baseline_files = file_map(baseline)
    candidate_files = file_map(candidate)
    baseline_paths = set(baseline_files)
    candidate_paths = set(candidate_files)

    removed = baseline_paths - candidate_paths
    added = candidate_paths - baseline_paths
    if removed != PLATFORM_REMOVED_PATHS:
        raise RuntimeError(
            f"unexpected removed paths: expected {sorted(PLATFORM_REMOVED_PATHS)}, got {sorted(removed)}"
        )
    if added != PRODUCT_ADDED_PATHS:
        raise RuntimeError(
            f"unexpected added paths: expected {sorted(PRODUCT_ADDED_PATHS)}, got {sorted(added)}"
        )

    missing_required = sorted(REQUIRED_PRODUCT_PATHS - candidate_paths)
    if missing_required:
        raise RuntimeError(f"required product paths are missing: {missing_required}")

    actual_changed = {
        relative
        for relative in baseline_paths & candidate_paths
        if baseline_files[relative].read_bytes() != candidate_files[relative].read_bytes()
    }
    undeclared_changes = sorted(actual_changed - declared_changed)
    if undeclared_changes:
        raise RuntimeError(f"undeclared product changes: {undeclared_changes}")

    unexpected_hook_loss = baseline_hooks - candidate_hooks - PLATFORM_ONLY_HOOKS
    if unexpected_hook_loss:
        raise RuntimeError(f"unexpected hook loss: {sorted(unexpected_hook_loss)}")
    if candidate_hooks & PLATFORM_ONLY_HOOKS:
        raise RuntimeError(f"platform-only hooks remain: {sorted(candidate_hooks & PLATFORM_ONLY_HOOKS)}")
    missing_direct_replacements = DIRECT_REPLACED_HOOKS - candidate_hooks
    if missing_direct_replacements:
        raise RuntimeError(f"direct replacement hooks are missing: {sorted(missing_direct_replacements)}")

    combined_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in candidate_files.values()
    )
    forbidden_found = sorted(marker for marker in FORBIDDEN_LEGACY_MARKERS if marker in combined_text)
    if forbidden_found:
        raise RuntimeError(f"legacy platform markers remain: {forbidden_found}")

    pyproject = (candidate / "pyproject.toml").read_text(encoding="utf-8")
    missing_configs = sorted(
        config for config in REQUIRED_TOOL_CONFIGS if f"[tool.{config}]" not in pyproject
    )
    if missing_configs:
        raise RuntimeError(f"required tool configuration is missing: {missing_configs}")

    precommit = (candidate / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    for marker in (
        "gitleaks",
        "markdownlint",
        "mdformat",
        "markdown-link-check",
        "typos",
        "bandit",
        "interrogate",
        "deptry",
        "check-manifest",
        "validate-pyproject",
        "pyproject-fmt",
        "dotenv-linter",
        "hadolint",
        "shellcheck",
        "pytest",
    ):
        if marker not in precommit:
            raise RuntimeError(f"required product hook is absent: {marker}")

    return {
        "baseline_file_count": len(baseline_paths),
        "candidate_file_count": len(candidate_paths),
        "removed_platform_paths": sorted(removed),
        "added_product_paths": sorted(added),
        "changed_paths": sorted(actual_changed),
        "byte_identical_paths": len((baseline_paths & candidate_paths) - actual_changed),
        "baseline_hook_count": len(baseline_hooks),
        "candidate_hook_count": len(candidate_hooks),
        "removed_platform_hooks": sorted(PLATFORM_ONLY_HOOKS),
        "retained_hook_ids": sorted(candidate_hooks),
    }


def initialize_git(root: Path) -> None:
    run("git init", ["git", "init", "-q"], cwd=root)
    run("git identity name", ["git", "config", "user.name", "Ternforge Lab"], cwd=root)
    run("git identity email", ["git", "config", "user.email", "lab@example.invalid"], cwd=root)
    run("git add", ["git", "add", "."], cwd=root)
    run("git commit", ["git", "commit", "-qm", "lab candidate"], cwd=root)


def run_product_checks(candidate: Path) -> list[CommandResult]:
    results: list[CommandResult] = []

    def checked(name: str, command: Sequence[str], *, env: dict[str, str] | None = None) -> None:
        results.append(run(name, command, cwd=candidate, env=env))

    checked("uv lock", ["uv", "lock"])
    checked("uv sync locked", ["uv", "sync", "--locked", "--all-groups"])
    initialize_git(candidate)

    checked("ruff lint", ["uv", "run", "--no-sync", "ruff", "check", "."])
    checked("ruff format", ["uv", "run", "--no-sync", "ruff", "format", "--check", "."])
    checked("ty", ["uv", "run", "--no-sync", "ty", "check", "--python", ".venv"])
    checked("pyright", ["uv", "run", "--no-sync", "pyright", "--project", "pyproject.toml"])
    checked(
        "import linter",
        ["uv", "run", "--no-sync", "lint-imports", "--config", "pyproject.toml"],
        env={"PYTHONPATH": "src:."},
    )
    checked("Ternforge policy", ["uv", "run", "--no-sync", "py-lib-policy", "."])
    checked(
        "cognitive complexity",
        [
            "uv",
            "run",
            "--no-sync",
            "flake8",
            "--select=CCR001",
            "--max-cognitive-complexity=15",
            "src",
        ],
    )
    checked(
        "class attribute order",
        [
            "uv",
            "run",
            "--no-sync",
            "flake8",
            "--select=CCE001",
            "--class-attributes-order=field,nested_class,magic_method,property_method,static_method,class_method,method",
            "src",
        ],
    )

    radon_cc = run(
        "radon cyclomatic complexity",
        ["uv", "run", "--no-sync", "radon", "cc", "--min", "C", "--show-complexity", "src"],
        cwd=candidate,
    )
    if radon_cc.stdout.strip():
        raise RuntimeError(f"radon cyclomatic complexity found failures:\n{radon_cc.stdout}")
    results.append(radon_cc)

    radon_mi = run(
        "radon maintainability",
        ["uv", "run", "--no-sync", "radon", "mi", "--min", "B", "--show", "src"],
        cwd=candidate,
    )
    if radon_mi.stdout.strip():
        raise RuntimeError(f"radon maintainability found failures:\n{radon_mi.stdout}")
    results.append(radon_mi)

    checked("bandit", ["uv", "run", "--no-sync", "bandit", "-c", "pyproject.toml", "-r", "src"])
    checked("interrogate", ["uv", "run", "--no-sync", "interrogate", "-c", "pyproject.toml"])
    checked("deptry", ["uv", "run", "--no-sync", "deptry", "--config", "pyproject.toml", "."])
    checked("policy tests", ["uv", "run", "--no-sync", "pytest", "tests", "-n", "auto", "-p", "randomly", "-m", "not slow", "-q", "--no-cov"])

    loop_probe = candidate / "workbench/sample_lib/_active_loop_probe.py"
    loop_probe.write_text(
        "# %%\nimport asyncio\nprint(type(asyncio.get_running_loop()).__name__)\n",
        encoding="utf-8",
    )
    try:
        checked(
            "active event-loop workbench diagnostic",
            [
                "uv",
                "run",
                "--no-sync",
                "python",
                "scripts/reproduce_running_loop.py",
                "workbench.sample_lib._active_loop_probe",
            ],
        )
    finally:
        loop_probe.unlink(missing_ok=True)

    runtime_requirements = candidate / ".runtime-requirements.txt"
    checked(
        "runtime export",
        [
            "uv",
            "export",
            "--frozen",
            "--no-dev",
            "--no-emit-project",
            "--no-emit-package",
            "py-lib-runtime",
            "--output-file",
            str(runtime_requirements),
        ],
    )
    checked(
        "runtime dependency audit",
        [
            "uv",
            "run",
            "--frozen",
            "--no-sync",
            "pip-audit",
            "--requirement",
            str(runtime_requirements),
            "--no-deps",
            "--disable-pip",
        ],
    )
    runtime_requirements.unlink(missing_ok=True)

    checked("build", ["uv", "build"])
    checked("twine metadata", ["uvx", "--from", "twine==6.2.0", "twine", "check", "dist/*"])
    checked(
        "wheel contents",
        ["uvx", "--from", "check-wheel-contents==0.6.3", "check-wheel-contents", "dist"],
    )
    checked("manifest", ["uv", "run", "--no-sync", "check-manifest", "--ignore", ".copier-answers.yml"])

    for artifact in sorted((candidate / "dist").iterdir()):
        if artifact.suffix not in {".whl", ".gz"}:
            continue
        venv = candidate / ".artifact-smoke" / artifact.name.replace(".", "_").replace("-", "_")
        checked("artifact venv", ["uv", "venv", str(venv)])
        checked(
            f"install {artifact.name}",
            ["uv", "pip", "install", "--python", str(venv / "bin" / "python"), str(artifact)],
        )
        checked(
            f"import {artifact.name}",
            [str(venv / "bin" / "python"), "-c", "import sample_lib; print(sample_lib.__version__)"],
        )

    checked(
        "pre-commit stage",
        ["uv", "run", "--no-sync", "pre-commit", "run", "--all-files", "--show-diff-on-failure"],
    )
    checked(
        "pre-push stage",
        [
            "uv",
            "run",
            "--no-sync",
            "pre-commit",
            "run",
            "--all-files",
            "--hook-stage",
            "pre-push",
            "--show-diff-on-failure",
        ],
    )
    checked("candidate remains clean", ["git", "diff", "--exit-code"])
    return results


def copy_snapshot(candidate: Path, snapshot: Path) -> None:
    if snapshot.exists():
        shutil.rmtree(snapshot)
    ignored = shutil.ignore_patterns(
        ".git",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        ".hypothesis",
        ".import_linter_cache",
        "__pycache__",
        "dist",
        "build",
        ".artifact-smoke",
        "uv.lock",
    )
    shutil.copytree(candidate, snapshot, ignore=ignored)


def write_evidence(
    *,
    evidence_json: Path,
    evidence_md: Path,
    static: dict[str, object],
    results: Iterable[CommandResult],
    snapshot: Path,
    snapshot_label: str,
) -> None:
    result_list = list(results)
    snapshot_files = file_map(snapshot)
    manifest = {relative: sha256(path) for relative, path in snapshot_files.items()}
    payload = {
        "schema": "ternforge-python-template-product-parity/v1",
        "baseline": {
            "repository": "betabitplus/py-lib-starter",
            "commit": BASELINE_SHA,
            "template": "python-lib-standard",
        },
        "candidate": {
            "purpose": "full product with platform-owned wiring replaced",
            "snapshot_path": snapshot_label,
            "snapshot_file_count": len(snapshot_files),
            "manifest": manifest,
        },
        "static_parity": static,
        "checks": [
            {
                "name": item.name,
                "returncode": item.returncode,
                "passed": item.passed,
            }
            for item in result_list
        ],
        "summary": {
            "all_checks_passed": all(item.passed for item in result_list),
            "check_count": len(result_list),
            "product_contract_preserved": True,
            "legacy_platform_markers_absent": True,
        },
    }
    evidence_json.parent.mkdir(parents=True, exist_ok=True)
    evidence_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Python template product parity lab",
        "",
        f"Frozen baseline: `betabitplus/py-lib-starter@{BASELINE_SHA}` / `python-lib-standard`.",
        "",
        "## Result",
        "",
        "The candidate keeps the generated Python-library product and replaces only platform-owned wiring.",
        "The committed render excludes `uv.lock`: Copier does not render it, while the experiment generates and validates it during bootstrap.",
        "",
        f"- baseline rendered files: **{static['baseline_file_count']}**",
        f"- candidate rendered files: **{static['candidate_file_count']}**",
        f"- byte-identical retained files: **{static['byte_identical_paths']}**",
        f"- retained product hooks: **{static['candidate_hook_count']}** of {static['baseline_hook_count']} baseline hooks",
        f"- executed checks: **{len(result_list)}**, all passed: **{all(item.passed for item in result_list)}**",
        f"- browsable candidate snapshot: `{snapshot_label}`",
        "",
        "## Removed platform-owned files",
        "",
        *[f"- `{path}`" for path in static["removed_platform_paths"]],
        "",
        "## Added product helper",
        "",
        *[f"- `{path}`" for path in static["added_product_paths"]],
        "",
        "The helper preserves the existing active-event-loop workbench diagnostic without retaining the legacy tooling monolith.",
        "",
        "## Removed platform-only hooks",
        "",
        *[f"- `{hook}`" for hook in static["removed_platform_hooks"]],
        "",
        "## Changed files",
        "",
        *[f"- `{path}`" for path in static["changed_paths"]],
        "",
        "## Executed checks",
        "",
        *[f"- {'PASS' if item.passed else 'FAIL'} — `{item.name}`" for item in result_list],
        "",
        "## Boundary proven",
        "",
        "- Product trees, documentation, tests, examples, workbench, devcontainer, editor settings, agent kit, quality/security configuration, and local hooks remain in the generated repository.",
        "- Old template assembly, local reusable CI bodies, CI image, template-sync workflow, branch-flow hooks, and legacy wrapper commands are absent.",
        "- Runtime, policy, and test support use the already validated split packages; generic checks call standard tools directly.",
        "",
    ]
    evidence_md.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--evidence-json", type=Path, required=True)
    parser.add_argument("--evidence-md", type=Path, required=True)
    parser.add_argument("--skip-product-checks", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_root = args.baseline_root.resolve()
    work_dir = args.work_dir.resolve()
    snapshot_label = args.snapshot_dir.as_posix()
    snapshot = args.snapshot_dir.resolve()
    evidence_json = args.evidence_json.resolve()
    evidence_md = args.evidence_md.resolve()

    baseline_render = work_dir / "baseline-render"
    candidate = work_dir / "candidate-render"
    work_dir.mkdir(parents=True, exist_ok=True)

    render_baseline(baseline_root, baseline_render)
    baseline_hooks, candidate_hooks, declared_changed = transform_candidate(baseline_render, candidate)
    static = verify_static_parity(
        baseline_render,
        candidate,
        baseline_hooks=baseline_hooks,
        candidate_hooks=candidate_hooks,
        declared_changed=declared_changed,
    )
    results: list[CommandResult] = []
    if not args.skip_product_checks:
        results = run_product_checks(candidate)
    copy_snapshot(candidate, snapshot)
    write_evidence(
        evidence_json=evidence_json,
        evidence_md=evidence_md,
        static=static,
        results=results,
        snapshot=snapshot,
        snapshot_label=snapshot_label,
    )
    print(json.dumps({"static": static, "checks": len(results), "snapshot": str(snapshot)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
