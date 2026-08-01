#!/usr/bin/env python3
"""Validate complete legacy product capability migration into Ternforge.

The experiment has four resumable phases because the four complete downstream
suites cannot reliably fit into one CI/client timeout:

1. ``prepare`` builds and tests runtime, policy, and testkit candidates and
   resolves every capability to preserved, standard replacement, or removal.
2. ``baseline`` runs the unchanged full suite of one frozen downstream repo.
3. ``migrate`` applies the clean one-time migration to that repo and reruns its
   full suite plus policy and import-linter.
4. ``finalize`` requires all four repos and emits immutable JSON/Markdown
   evidence. It does not modify any source repository.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

BASELINE_SHA = "d59582375855cff69fb165e467dc5847bc75ca99"
RUNTIME_SHA = "a4fa84809aa9c5aced3c0a367b23fbcc7f5466d0"
POLICY_SHA = "d44737a0887c6bf5d8702d03221845c62e0fed4b"
TESTKIT_SHA = "233ebec6a1106fd1b65b84803019494522338667"
CONSUMER_SHAS = {
    "llm-router": "6e8008a26a3d1b167befa1ca87b25386b10e4308",
    "reddit-scraper": "c4e5b74b035666d434366ed85a5f447a45d29ea1",
    "visual-annotation": "06e5e00bb50f2808e223e0d985a41725ba01298a",
    "web-tools": "b0894c8a99598a827a42909c739ff7136d370d38",
}
ALLOWED_DISPOSITIONS = {"preserved", "standard_replacement", "intentional_removal"}
LEGACY_TESTKIT_TESTS = (
    "packages/py-lib-tooling/tests/py_lib_tooling/unit/test_demo_console_json_rendering.py",
    "packages/py-lib-tooling/tests/py_lib_tooling/unit/test_project_config.py",
    "packages/py-lib-tooling/tests/py_lib_tooling/unit/test_test_support_images.py",
    "packages/py-lib-tooling/tests/py_lib_tooling/unit/test_test_support_paths.py",
    "packages/py-lib-tooling/tests/py_lib_tooling/unit/test_test_support_setup.py",
    "packages/py-lib-tooling/tests/py_lib_tooling/unit/test_vcr_support.py",
)
USER_OWNED_ROOTS = ("src", "tests", "examples", "workbench", "docs")
LEGACY_ANSWER_KEYS = (
    "ci_image_copy_paths",
    "runtime_git_ref",
    "runtime_git_subdirectory",
    "runtime_git_url",
    "tooling_git_ref",
    "tooling_git_subdirectory",
    "tooling_git_url",
)
_SPLIT_LOCK_PACKAGES = {
    "py-lib-runtime",
    "py-lib-tooling",
    "py-lib-policy",
    "py-lib-testkit",
}
_MANAGED_TEMPLATE_PATHS = (
    ".agents",
    ".devcontainer",
    ".github",
    ".vscode",
    ".envrc",
    ".gitleaks.toml",
    ".markdown-link-check.json",
    ".markdownlint.yaml",
    ".mdformat.toml",
    ".pre-commit-config.yaml",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "MANIFEST.in",
    "renovate.json5",
    "RTK.md",
    "SETUP.md",
    "scripts",
    "typos.toml",
)
_FORBIDDEN_LEGACY_REFERENCES = (
    "py_lib_tooling",
    "py-lib-tooling",
    "py_lib_starter",
    "py-lib-starter",
    "py_lib_testkit._internal.quality_gates",
    "py_lib_testkit._internal.template",
    "py_lib_testkit._internal.smoke",
    "py-lib-check-",
    "py-lib-smoke-",
    "py-lib-template-",
    "py-lib-project-info",
    "py-lib-refresh-shared-lock",
    "py-lib-reproduce-running-loop",
    "py-lib-platform-",
    "py-lib-create-managed-repository",
)

RESOLUTIONS: dict[str, dict[str, str]] = {
    "TPL-03": {
        "status": "preserved",
        "current": "required standalone build/test/install acceptance for runtime, policy, and testkit repositories",
        "evidence": "EXP candidate runs full package tests and uv build from each independent repository root",
    },
    "TPL-08": {
        "status": "intentional_removal",
        "current": "Ternforge typed records and repository-local runbooks",
        "evidence": "starter-docs-rules exists only for the removed py-lib-starter platform monorepo taxonomy and conflicts with the typed-record model",
    },
    "POL-05": {
        "status": "preserved",
        "current": "py-lib-policy reads [tool.ternforge], exact package_names/primary_package, public namespaces, and uv workspaces",
        "evidence": "candidate positive/negative tests include non-default distribution/package names and two workspace members",
    },
    "POL-06": {
        "status": "preserved",
        "current": "py-lib-policy exact source/API/config/test skeleton and root namespace rules",
        "evidence": "candidate tests cover every retained structural rule and all migrated consumers must pass policy",
    },
    "POL-07": {
        "status": "preserved",
        "current": "py-lib-policy declaration modules, facade shape, flat-private, and root-only __all__ rules",
        "evidence": "candidate focused tests cover config/defaults/errors/types/_api init/product facade/__all__ behavior",
    },
    "POL-08": {
        "status": "preserved",
        "current": "py-lib-policy keeps example placement, cell-marker, and private string-reference rules; import-linter owns static imports",
        "evidence": "candidate explicitly proves retained rules and proves generic static imports are not duplicated",
    },
    "POL-09": {
        "status": "preserved",
        "current": "py-lib-policy checks runnable e2e and workbench cell markers",
        "evidence": "candidate positive/negative tests and migrated-consumer policy runs",
    },
    "POL-10": {
        "status": "preserved",
        "current": "py-lib-policy keeps the complete docs skeleton and YAML e2e_slices path/document contract using PyYAML",
        "evidence": "candidate tests cover all package docs, custom e2e slices, malformed YAML semantics, and real consumer answers",
    },
    "KIT-02": {
        "status": "preserved",
        "current": "py-lib-testkit owns complete Ternforge project test/workbench configuration semantics",
        "evidence": "candidate uses [tool.ternforge] and preserves distribution/package/env/logging/VCR behavior",
    },
    "KIT-03": {
        "status": "preserved",
        "current": "py_lib_testkit.get_project_tooling_config with the full ProjectToolingConfig contract",
        "evidence": "candidate public API tests plus full reddit-scraper, visual-annotation, and web-tools suites",
    },
    "KIT-04": {
        "status": "preserved",
        "current": "py_lib_testkit.get_repo_root with fail-closed upward pyproject discovery",
        "evidence": "candidate tests plus full llm-router and visual-annotation suites",
    },
    "KIT-05": {
        "status": "preserved",
        "current": "py-lib-testkit configure_direct_module_process with complete runtime logging configuration",
        "evidence": "legacy setup tests and candidate regression test execute the logging branch without AttributeError",
    },
    "KIT-06": {
        "status": "preserved",
        "current": "py-lib-testkit run_async with an explicit nest-asyncio dependency",
        "evidence": "candidate executes run_async from inside an active event loop",
    },
    "KIT-07": {
        "status": "preserved",
        "current": "repository-specific <ENV_PREFIX>_MULTIPART_SIGNATURE bytes",
        "evidence": "candidate config and VCR tests preserve the frozen behavior used by llm-router",
    },
    "KIT-08": {
        "status": "preserved",
        "current": "testkit repository carries the transformed test-support usage documentation",
        "evidence": "candidate copies the complete legacy test-support guide under the new package identity",
    },
    "KIT-09": {
        "status": "preserved",
        "current": "one-time atomic consumer migration from py_lib_tooling to py_lib_testkit; no permanent compatibility package",
        "evidence": "all user-owned imports in four frozen consumers are migrated and the exact complete suites retain pass/skip counts",
    },
    "UPD-04": {
        "status": "preserved",
        "current": "explicit one-time answers/provenance migration to ternforge-template-py-library",
        "evidence": "experiment rewrites _src_path/_commit, removes legacy source fields, regenerates uv.lock, and rejects residual user-owned legacy imports",
    },
    "OPS-05": {
        "status": "standard_replacement",
        "current": "OpenTofu plan/apply plus bootstrap CI/ruleset sequencing",
        "evidence": "dry-run becomes tofu plan; resumability/idempotence become declarative re-apply; validation is required CI before phase-two rulesets; legacy PR-reuse orchestration is removed",
    },
    "OPS-06": {
        "status": "preserved",
        "current": "released Python template remains usable outside the managed fleet; repository-control automation is optional",
        "evidence": "standalone product capability is retained while the py-lib-starter-specific App setup script is not migrated",
    },
    "OPS-10": {
        "status": "intentional_removal",
        "current": "GitHub-hosted CI with no custom runner image or runner lifecycle control plane",
        "evidence": "the fallback exists only for legacy py-lib-starter infrastructure and contradicts the chosen hosted, direct-tool CI model",
    },
    "OPS-13": {
        "status": "preserved",
        "current": "one workflow/ruleset model across visibility states; visibility changes access scope, not product workflow topology",
        "evidence": "scoped App credentials and repository-control visibility fields preserve the contract without local runner branching",
    },
    "OPS-14": {
        "status": "preserved",
        "current": "implementation-owned bootstrap, recovery, rollback, and credential-boundary runbooks",
        "evidence": "runbooks remain a required implementation deliverable; only the legacy starter taxonomy is removed",
    },
}


def _run(command: list[str], *, cwd: Path, timeout: int = 1800) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    result = {
        "command": command,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}) in {cwd}: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return result


def _git_revision(path: Path) -> str:
    return _run(["git", "rev-parse", "HEAD"], cwd=path)["stdout"].strip()


def _assert_revision(path: Path, expected: str, label: str) -> None:
    actual = _git_revision(path)
    if actual != expected:
        raise RuntimeError(f"{label} revision mismatch: expected {expected}, got {actual}")


def _copytree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            "*.egg-info",
            "dist",
            "build",
        ),
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_state(output: Path) -> dict[str, Any]:
    path = output / "state.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _save_state(output: Path, state: dict[str, Any]) -> None:
    _write_json(output / "state.json", state)


def _parse_pytest(output: str) -> dict[str, int]:
    matches = list(re.finditer(r"(?P<passed>\d+) passed(?:, (?P<skipped>\d+) skipped)?", output))
    if not matches:
        raise RuntimeError(f"could not parse pytest summary:\n{output[-2000:]}")
    match = matches[-1]
    return {
        "passed": int(match.group("passed")),
        "skipped": int(match.group("skipped") or 0),
    }


def _replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one occurrence in {path}: {old!r}; got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _resolve_matrix(inventory: Path) -> list[dict[str, Any]]:
    matrix = json.loads(inventory.read_text(encoding="utf-8"))
    if not isinstance(matrix, list):
        raise TypeError("capability inventory must be a list")
    seen: set[str] = set()
    for item in matrix:
        identifier = item.get("id")
        if not isinstance(identifier, str) or identifier in seen:
            raise ValueError(f"invalid or duplicate capability id: {identifier!r}")
        seen.add(identifier)
        if identifier in RESOLUTIONS:
            item.update(RESOLUTIONS[identifier])
        if item.get("status") not in ALLOWED_DISPOSITIONS:
            raise ValueError(f"capability {identifier} has forbidden disposition {item.get('status')!r}")
    missing = sorted(set(RESOLUTIONS) - seen)
    if missing:
        raise ValueError(f"resolution ids missing from inventory: {missing}")
    return matrix


def _normalized_runtime_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return re.sub(r'__version__ = "[^"]+"', '__version__ = "<VERSION>"', text)


def _verify_runtime_source_parity(legacy: Path, candidate: Path) -> dict[str, int]:
    legacy_root = legacy / "packages/py-lib-runtime/src/py_lib_runtime"
    candidate_root = candidate / "src/py_lib_runtime"
    legacy_files = {path.relative_to(legacy_root) for path in legacy_root.rglob("*.py")}
    candidate_files = {path.relative_to(candidate_root) for path in candidate_root.rglob("*.py")}
    if legacy_files != candidate_files:
        raise RuntimeError(
            f"runtime source file set differs: missing={sorted(legacy_files-candidate_files)}, extra={sorted(candidate_files-legacy_files)}"
        )
    for relative in sorted(legacy_files):
        if _normalized_runtime_text(legacy_root / relative) != _normalized_runtime_text(candidate_root / relative):
            raise RuntimeError(f"runtime source differs beyond version metadata: {relative}")
    return {"python_files": len(legacy_files)}


def _build_runtime_candidate(args: argparse.Namespace, work: Path) -> dict[str, Any]:
    destination = work / "py-lib-runtime"
    _copytree(args.runtime, destination)
    parity = _verify_runtime_source_parity(args.legacy, destination)
    tests = _run(["uv", "run", "--frozen", "pytest"], cwd=destination)
    build = _run(["uv", "build"], cwd=destination)
    return {"parity": parity, "tests": _parse_pytest(tests["stdout"]), "build": build["returncode"]}


def _build_policy_candidate(args: argparse.Namespace, work: Path) -> dict[str, Any]:
    destination = work / "py-lib-policy"
    _copytree(args.policy, destination)
    shutil.rmtree(destination / "tests", ignore_errors=True)
    (destination / "tests").mkdir()
    shutil.copy2(args.assets / "policy_candidate.py", destination / "py_lib_policy.py")
    shutil.copy2(args.assets / "policy_candidate_tests.py", destination / "tests/test_complete_policy.py")
    _replace_once(destination / "pyproject.toml", "dependencies = []", 'dependencies = ["PyYAML>=6.0.3"]')
    (destination / "uv.lock").unlink(missing_ok=True)
    _run(["uv", "lock"], cwd=destination)
    tests = _run(["uv", "run", "--frozen", "pytest"], cwd=destination)
    build = _run(["uv", "build"], cwd=destination)
    return {"tests": _parse_pytest(tests["stdout"]), "build": build["returncode"], "dependencies": ["PyYAML>=6.0.3"]}


def _transform_legacy_source(text: str) -> str:
    return (
        text.replace("py_lib_tooling", "py_lib_testkit")
        .replace("py-lib-tooling", "py-lib-testkit")
        .replace("PY_LIB_TOOLING", "PY_LIB_TESTKIT")
        .replace("py_lib_starter", "ternforge")
        .replace("py-lib-starter", "Ternforge")
    )


def _transform_legacy_test(source: Path, destination: Path) -> None:
    destination.write_text(
        _transform_legacy_source(source.read_text(encoding="utf-8")),
        encoding="utf-8",
    )


def _verify_test_support_code(legacy: Path, candidate: Path) -> dict[str, int]:
    legacy_root = legacy / "packages/py-lib-tooling/src/py_lib_tooling/_internal/test_support"
    candidate_root = candidate / "src/py_lib_testkit/_internal/test_support"
    files = sorted(path.name for path in legacy_root.glob("*.py"))
    for name in files:
        left = (legacy_root / name).read_text(encoding="utf-8").replace("py_lib_tooling", "py_lib_testkit")
        right = (candidate_root / name).read_text(encoding="utf-8")
        if left != right:
            raise RuntimeError(f"test-support implementation changed unexpectedly: {name}")
    return {"modules": len(files)}


def _build_testkit_candidate(args: argparse.Namespace, work: Path) -> dict[str, Any]:
    destination = work / "py-lib-testkit"
    _copytree(args.testkit, destination)
    config_module = destination / "src/py_lib_testkit/_internal/config.py"
    config_module.unlink()
    legacy_config = args.legacy / "packages/py-lib-tooling/src/py_lib_tooling/_internal/config"
    candidate_config = destination / "src/py_lib_testkit/_internal/config"
    candidate_config.mkdir()
    for source in sorted(legacy_config.glob("*.py")):
        (candidate_config / source.name).write_text(
            _transform_legacy_source(source.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
    legacy_defaults = args.legacy / "packages/py-lib-tooling/src/py_lib_tooling/_api/defaults.py"
    (destination / "src/py_lib_testkit/_api/defaults.py").write_text(
        _transform_legacy_source(legacy_defaults.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    shutil.copy2(args.assets / "testkit_api_config_candidate.py", destination / "src/py_lib_testkit/_api/config.py")
    shutil.copy2(args.assets / "testkit_root_candidate.py", destination / "src/py_lib_testkit/__init__.py")

    pyproject = destination / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text = text.replace('  "ipython>=9",', '  "ipython>=9",\n  "nest-asyncio>=1.6",')
    text = re.sub(
        r"\n\[tool\.uv\.sources\]\n.*?(?=\n\[dependency-groups\])",
        '\n[tool.uv.sources]\npy-lib-runtime = { path = "../py-lib-runtime" }\n',
        text,
        flags=re.S,
    )
    text = text.replace("[tool.py_lib_starter]", "[tool.ternforge]")
    text = text.replace('primary_package = "py_lib_testkit"\nenv_prefix', 'primary_package = "py_lib_testkit"\npackage_names = ["py_lib_testkit"]\nlibrary_lane = "standard-lib"\nenv_prefix')
    pyproject.write_text(text, encoding="utf-8")

    tests = destination / "tests"
    for index, relative in enumerate(LEGACY_TESTKIT_TESTS, start=1):
        _transform_legacy_test(args.legacy / relative, tests / f"test_legacy_{index:02d}.py")
    shutil.copy2(args.assets / "testkit_candidate_tests.py", tests / "test_complete_contract.py")

    docs_source = args.legacy / "packages/py-lib-tooling/docs/py_lib_tooling/test-support-usage.md"
    docs_target = destination / "docs/py_lib_testkit/test-support-usage.md"
    docs_target.parent.mkdir(parents=True, exist_ok=True)
    docs_target.write_text(
        docs_source.read_text(encoding="utf-8")
        .replace("py_lib_tooling", "py_lib_testkit")
        .replace("py-lib-tooling", "py-lib-testkit"),
        encoding="utf-8",
    )

    code_parity = _verify_test_support_code(args.legacy, destination)
    (destination / "uv.lock").unlink(missing_ok=True)
    _run(["uv", "lock"], cwd=destination)
    test_result = _run(["uv", "run", "--frozen", "pytest"], cwd=destination)
    build = _run(["uv", "build"], cwd=destination)
    return {
        "code_parity": code_parity,
        "tests": _parse_pytest(test_result["stdout"]),
        "build": build["returncode"],
        "explicit_dependencies": ["nest-asyncio>=1.6", "py-lib-runtime"],
    }


def _prepare(args: argparse.Namespace) -> None:
    if args.output.exists():
        shutil.rmtree(args.output)
    work = args.output / "_work"
    work.mkdir(parents=True)

    _assert_revision(args.legacy, BASELINE_SHA, "legacy baseline")
    _assert_revision(args.runtime, RUNTIME_SHA, "runtime prototype")
    _assert_revision(args.policy, POLICY_SHA, "policy prototype")
    _assert_revision(args.testkit, TESTKIT_SHA, "testkit prototype")

    matrix = _resolve_matrix(args.inventory)
    _write_json(args.output / "migration-matrix.json", matrix)
    state = {
        "schema": "ternforge-product-capability-parity/v1",
        "revisions": {
            "legacy": BASELINE_SHA,
            "runtime": RUNTIME_SHA,
            "policy": POLICY_SHA,
            "testkit": TESTKIT_SHA,
            "consumers": CONSUMER_SHAS,
        },
        "matrix_counts": dict(Counter(item["status"] for item in matrix)),
        "packages": {},
        "consumers": {},
    }
    state["packages"]["runtime"] = _build_runtime_candidate(args, work)
    state["packages"]["policy"] = _build_policy_candidate(args, work)
    state["packages"]["testkit"] = _build_testkit_candidate(args, work)
    _save_state(args.output, state)


def _consumer_name(path: Path, explicit: str | None) -> str:
    name = explicit or path.name.removeprefix("consumer-")
    if name not in CONSUMER_SHAS:
        raise ValueError(f"unknown consumer {name!r}; expected one of {sorted(CONSUMER_SHAS)}")
    return name


def _baseline(args: argparse.Namespace) -> None:
    if args.consumer is None:
        raise ValueError("baseline requires --consumer")
    name = _consumer_name(args.consumer, args.name)
    _assert_revision(args.consumer, CONSUMER_SHAS[name], name)
    result = _run(["uv", "run", "--frozen", "pytest", "-q"], cwd=args.consumer)
    state = _load_state(args.output)
    state.setdefault("consumers", {}).setdefault(name, {})["baseline"] = _parse_pytest(result["stdout"])
    state["consumers"][name]["revision"] = CONSUMER_SHAS[name]
    _save_state(args.output, state)


def _consumer_identity(root: Path) -> dict[str, str]:
    with (root / "pyproject.toml").open("rb") as stream:
        raw = tomllib.load(stream)
    project = raw.get("project")
    tool = raw.get("tool")
    if not isinstance(project, dict) or not isinstance(tool, dict):
        raise TypeError(f"{root / 'pyproject.toml'} must define [project] and [tool]")
    ternforge = tool.get("py_lib_starter") or tool.get("ternforge")
    if not isinstance(ternforge, dict):
        raise TypeError(f"{root / 'pyproject.toml'} must define the project tooling table")
    answers = yaml.safe_load((root / "_copier_answers.yml").read_text(encoding="utf-8"))
    if not isinstance(answers, dict):
        raise TypeError(f"{root / '_copier_answers.yml'} must contain a mapping")

    def required(table: dict[str, Any], key: str) -> str:
        value = table.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"missing non-empty {key!r} in {root}")
        return value

    distribution_name = required(project, "name")
    return {
        "distribution_name": distribution_name,
        "primary_package": required(ternforge, "primary_package"),
        "env_prefix": required(ternforge, "env_prefix"),
        "project_title": str(answers.get("project_title") or distribution_name.replace("-", " ").title()),
    }


def _render_candidate_text(text: str, identity: dict[str, str]) -> str:
    return (
        text.replace("SAMPLE_LIB", identity["env_prefix"])
        .replace("Sample Lib", identity["project_title"])
        .replace("sample_lib", identity["primary_package"])
        .replace("sample-lib", identity["distribution_name"])
    )


def _replace_managed_surface(
    root: Path,
    *,
    candidate: Path,
    identity: dict[str, str],
) -> list[str]:
    if not candidate.is_dir():
        raise FileNotFoundError(f"template candidate is missing: {candidate}")
    copied: list[str] = []
    for relative in _MANAGED_TEMPLATE_PATHS:
        source = candidate / relative
        target = root / relative
        if not source.exists():
            raise FileNotFoundError(f"managed candidate path is missing: {source}")
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        copied.append(relative)

    for relative in copied:
        target = root / relative
        paths = target.rglob("*") if target.is_dir() else (target,)
        for path in paths:
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            rendered = _render_candidate_text(text, identity)
            if rendered != text:
                path.write_text(rendered, encoding="utf-8")
    return copied


def _replace_text_files(root: Path, *, identity: dict[str, str]) -> int:
    replacements = (
        (
            "uv run py-lib-smoke-public-api",
            f"uv run pytest tests/{identity['primary_package']}/e2e/public_boundary -q --no-cov",
        ),
        ("uv run py-lib-smoke-installed-artifact", "uv build"),
        ("uv run py-lib-smoke-built-artifacts", "uv build"),
        ("uv run py-lib-template-check", "uvx --from copier==9.17.0 copier check-update"),
        ("uv run py-lib-template-update", "uvx --from copier==9.17.0 copier update"),
        ("uv run py-lib-reproduce-running-loop", "uv run python scripts/reproduce_running_loop.py"),
        ("uv run py-lib-check-legacy-support-cleanup", "uv run py-lib-policy ."),
        ("uv run py-lib-check-project-docs-structure", "uv run py-lib-policy ."),
        ("uv run py-lib-check-project-structure --strict-template", "uv run py-lib-policy ."),
        (
            "uv run py-lib-check-public-contract-private-references",
            "uv run lint-imports --config pyproject.toml",
        ),
        ("py-lib-check-cognitive-complexity", "cognitive-complexity"),
        ("py-lib-check-class-attributes-order", "class-attributes-order"),
        ("py-lib-audit-runtime-dependencies", "runtime-dependency-audit"),
        ("py-lib-check-project-docs-structure", "ternforge-policy-docs"),
        ("py-lib-check-project-structure", "ternforge-policy-structure"),
        ("py-lib-check-public-contract-boundary", "lint-imports --config pyproject.toml"),
        ("py-lib-project-info", "uv version"),
        ("https://github.com/betabitplus/py-lib-starter.git", "https://github.com/betabitplus/ternforge-template-py-library.git"),
        ("betabitplus/py-lib-starter", "betabitplus/ternforge-template-py-library"),
        ("py_lib_tooling", "py_lib_testkit"),
        ("py-lib-tooling", "py-lib-testkit"),
        ("[tool.py_lib_starter]", "[tool.ternforge]"),
        ("tool.py_lib_starter", "tool.ternforge"),
        ("py_lib_starter", "ternforge"),
        ("py-lib-starter", "Ternforge"),
    )
    changed = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in {".git", ".venv"} for part in path.parts):
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
            changed += 1
    return changed


def _forbidden_legacy_references(root: Path) -> list[str]:
    matches: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in {".git", ".venv"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in _FORBIDDEN_LEGACY_REFERENCES:
            if pattern in text:
                matches.append(f"{path.relative_to(root)}: {pattern}")
    return matches


def _verify_managed_surface(root: Path) -> dict[str, Any]:
    workflows = root / ".github/workflows"
    workflow_files = sorted(path.name for path in workflows.glob("*.yml"))
    if workflow_files != ["ci.yml", "release.yml"]:
        raise RuntimeError(f"unexpected managed workflow set: {workflow_files}")
    ci_text = (workflows / "ci.yml").read_text(encoding="utf-8")
    release_text = (workflows / "release.yml").read_text(encoding="utf-8")
    if "ternforge-infra-ci/.github/workflows/python-library.yml@" not in ci_text:
        raise RuntimeError("CI is not a thin Ternforge reusable-workflow caller")
    if "ternforge-infra-ci/.github/workflows/release.yml@" not in release_text:
        raise RuntimeError("Release is not a thin Ternforge reusable-workflow caller")
    if not (root / ".pre-commit-config.yaml").is_file():
        raise RuntimeError("managed pre-commit configuration is missing")
    forbidden = _forbidden_legacy_references(root)
    if forbidden:
        raise RuntimeError(f"forbidden legacy references remain: {forbidden}")
    return {
        "workflow_files": workflow_files,
        "thin_ci_caller": True,
        "thin_release_caller": True,
        "forbidden_legacy_references": [],
    }


def _migrate_answers(root: Path) -> dict[str, Any]:
    path = root / "_copier_answers.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a mapping")
    removed: list[str] = []
    for key in LEGACY_ANSWER_KEYS:
        if key in data:
            removed.append(key)
            data.pop(key)
    data["_src_path"] = "https://github.com/betabitplus/ternforge-template-py-library.git"
    data["_commit"] = "v0.1.0-lab"
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return {"removed_keys": sorted(removed), "source": data["_src_path"], "commit": data["_commit"]}


def _rewrite_consumer_pyproject(root: Path, work: Path) -> None:
    path = root / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    runtime_uri = (work / "py-lib-runtime").resolve().as_uri()
    policy_uri = (work / "py-lib-policy").resolve().as_uri()
    testkit_uri = (work / "py-lib-testkit").resolve().as_uri()
    text, runtime_count = re.subn(
        r'  "py-lib-runtime @ git\+[^\n]+",',
        f'  "py-lib-runtime @ {runtime_uri}",',
        text,
        count=1,
    )
    text, tooling_count = re.subn(
        r'  "py-lib-tooling @ git\+[^\n]+",',
        f'  "py-lib-policy @ {policy_uri}",\n  "py-lib-testkit @ {testkit_uri}",',
        text,
        count=1,
    )
    if runtime_count != 1 or tooling_count != 1:
        raise RuntimeError(f"could not rewrite split dependencies in {path}: runtime={runtime_count}, tooling={tooling_count}")
    text = text.replace("[tool.py_lib_starter]", "[tool.ternforge]")
    path.write_text(text, encoding="utf-8")


def _user_owned_legacy_references(root: Path) -> list[str]:
    matches: list[str] = []
    for directory in USER_OWNED_ROOTS:
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if "py_lib_tooling" in text or "py-lib-tooling" in text:
                matches.append(path.relative_to(root).as_posix())
    return sorted(matches)


def _public_import_names(root: Path, module: str) -> list[str]:
    names: set[str] = set()
    for directory in USER_OWNED_ROOTS:
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == module:
                    names.update(alias.name for alias in node.names)
    return sorted(names)


def _project_distribution_name(root: Path) -> str:
    with (root / "pyproject.toml").open("rb") as stream:
        raw = tomllib.load(stream)
    project = raw.get("project")
    if not isinstance(project, dict):
        raise TypeError(f"{root / 'pyproject.toml'} must define [project]")
    name = project.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"{root / 'pyproject.toml'} [project].name must be a non-empty string")
    return name


def _unrelated_lock_entries(root: Path, *, project_name: str) -> list[dict[str, Any]]:
    with (root / "uv.lock").open("rb") as stream:
        raw = tomllib.load(stream)
    packages = raw.get("package")
    if not isinstance(packages, list):
        raise TypeError(f"{root / 'uv.lock'} must contain package entries")
    excluded = {*_SPLIT_LOCK_PACKAGES, project_name}
    entries = [package for package in packages if isinstance(package, dict) and package.get("name") not in excluded]
    return sorted(
        entries,
        key=lambda package: (
            str(package.get("name", "")),
            str(package.get("version", "")),
            json.dumps(package.get("source", {}), sort_keys=True),
        ),
    )


def _migrate(args: argparse.Namespace) -> None:
    if args.consumer is None:
        raise ValueError("migrate requires --consumer")
    name = _consumer_name(args.consumer, args.name)
    _assert_revision(args.consumer, CONSUMER_SHAS[name], name)
    state = _load_state(args.output)
    baseline = state.get("consumers", {}).get(name, {}).get("baseline")
    if baseline is None:
        raise RuntimeError(f"run baseline for {name} first")

    work = args.output / "_work"
    for package in ("py-lib-runtime", "py-lib-policy", "py-lib-testkit"):
        if not (work / package).is_dir():
            raise RuntimeError("prepare phase is missing candidate packages")

    destination = work / f"consumer-{name}"
    _copytree(args.consumer, destination)
    identity = _consumer_identity(destination)
    project_name = _project_distribution_name(destination)
    lock_before = _unrelated_lock_entries(destination, project_name=project_name)
    managed_paths = _replace_managed_surface(
        destination,
        candidate=args.template_candidate,
        identity=identity,
    )
    _rewrite_consumer_pyproject(destination, work)
    answers = _migrate_answers(destination)
    changed_files = _replace_text_files(destination, identity=identity)
    _run(["uv", "lock"], cwd=destination)
    lock_after = _unrelated_lock_entries(destination, project_name=project_name)
    def artifact_key(item: dict[str, Any]) -> str:
        dependency_targets = []
        for dependency in item.get("dependencies", []):
            if isinstance(dependency, dict):
                dependency_targets.append(
                    {key: value for key, value in dependency.items() if key != "marker"}
                )
        payload = {
            "name": item.get("name"),
            "version": item.get("version"),
            "source": item.get("source"),
            "sdist": item.get("sdist"),
            "wheels": item.get("wheels"),
            "dependency_targets": sorted(
                dependency_targets,
                key=lambda value: json.dumps(value, sort_keys=True),
            ),
        }
        return json.dumps(payload, sort_keys=True)

    before_entries = {artifact_key(item): item for item in lock_before}
    after_entries = {artifact_key(item): item for item in lock_after}
    added_entries = [after_entries[key] for key in sorted(set(after_entries) - set(before_entries))]
    if added_entries:
        added_names = sorted({str(item.get("name")) for item in added_entries})
        raise RuntimeError(f"unrelated lock artifacts or dependency targets changed for {name}: {added_names}")
    removed_entries = [before_entries[key] for key in sorted(set(before_entries) - set(after_entries))]
    removed_lock_names = sorted({str(item.get("name")) for item in removed_entries})
    normalized_lock_names = sorted(
        str(before_entries[key].get("name"))
        for key in set(before_entries) & set(after_entries)
        if before_entries[key] != after_entries[key]
    )

    residual = _user_owned_legacy_references(destination)
    if residual:
        raise RuntimeError(f"legacy tooling references remain in user-owned files for {name}: {residual}")

    managed_surface = _verify_managed_surface(destination)
    policy = _run([str(work / "py-lib-policy/.venv/bin/py-lib-policy"), str(destination)], cwd=destination)
    imports = _run(["uv", "run", "--frozen", "lint-imports", "--config", "pyproject.toml"], cwd=destination)
    tests = _run(["uv", "run", "--frozen", "pytest", "-q"], cwd=destination)
    migrated = _parse_pytest(tests["stdout"])
    if migrated != baseline:
        raise RuntimeError(f"consumer {name} test counts changed: baseline={baseline}, migrated={migrated}")

    result = {
        "baseline": baseline,
        "migrated": migrated,
        "changed_text_files": changed_files,
        "managed_template_paths_replaced": managed_paths,
        "managed_surface": managed_surface,
        "answers": answers,
        "unrelated_lock_entries_preserved": len(lock_after),
        "removed_legacy_transitive_lock_packages": removed_lock_names,
        "normalized_lock_metadata_packages": normalized_lock_names,
        "policy": policy["returncode"],
        "import_linter": imports["returncode"],
        "testkit_public_imports": _public_import_names(destination, "py_lib_testkit"),
        "residual_user_owned_legacy_references": residual,
    }
    state.setdefault("consumers", {}).setdefault(name, {}).update(result)
    _save_state(args.output, state)
    shutil.rmtree(destination)


def _report(state: dict[str, Any], matrix: list[dict[str, Any]]) -> str:
    lines = [
        "# Complete product capability parity",
        "",
        "## Result",
        "",
        "PASS. Every inventoried legacy capability has exactly one accepted disposition, split packages pass independent acceptance, and all four frozen downstream suites retain exact results after the atomic migration.",
        "",
        "## Capability dispositions",
        "",
        "| Disposition | Count |",
        "|---|---:|",
    ]
    counts = Counter(item["status"] for item in matrix)
    for status in ("preserved", "standard_replacement", "intentional_removal"):
        lines.append(f"| `{status}` | {counts[status]} |")
    lines.extend(
        [
            "",
            "No unresolved, deferred, representative-only, or sample-only disposition is allowed.",
            "",
            "## Split packages",
            "",
            "| Package | Tests | Build |",
            "|---|---:|---:|",
        ]
    )
    for name in ("runtime", "policy", "testkit"):
        package = state["packages"][name]
        summary = package["tests"]
        lines.append(f"| `{name}` | {summary['passed']} passed, {summary['skipped']} skipped | PASS |")
    lines.extend(
        [
            "",
            "## Frozen downstream repositories",
            "",
            "| Repository | Revision | Baseline | Migrated | Policy | Import boundaries |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    total_passed = 0
    total_skipped = 0
    for name in sorted(CONSUMER_SHAS):
        consumer = state["consumers"][name]
        baseline = consumer["baseline"]
        migrated = consumer["migrated"]
        total_passed += migrated["passed"]
        total_skipped += migrated["skipped"]
        lines.append(
            f"| `{name}` | `{CONSUMER_SHAS[name][:12]}` | "
            f"{baseline['passed']}/{baseline['skipped']} | {migrated['passed']}/{migrated['skipped']} | PASS | PASS |"
        )
    lines.extend(
        [
            "",
            f"Total downstream result: **{total_passed} passed, {total_skipped} skipped**, unchanged before and after migration.",
            "",
            "## Accepted clean migration contract",
            "",
            "* Runtime remains behaviorally identical to the frozen product package.",
            "* Policy keeps all Ternforge-specific structure, declaration, configuration, docs, e2e-slice, runnable-example, test, and workbench rules. Generic imports remain in import-linter/Ruff/Pyright.",
            "* Policy uses PyYAML instead of a custom YAML parser because e2e_slices is an active downstream contract.",
            "* Testkit preserves the complete public config/root/test-support surface, runtime logging, active-loop, VCR, image, path, console, and repository-specific multipart behavior.",
            "* Consumers move atomically: dependencies, public imports, [tool.ternforge], answers provenance, managed template surface, and lockfile change together. There is no permanent py_lib_tooling compatibility package and no dual config table.",
            "* Template-owned workflows, pre-commit, agents, scripts, setup and repository configuration come from the latest accepted hardening render; every migrated repository has only thin ci.yml/release.yml callers and zero forbidden legacy CLI/internal references.",
            "* Only legacy py-lib-starter infrastructure that conflicts with the selected Ternforge model is removed.",
            "",
        ]
    )
    return "\n".join(lines)


def _finalize(args: argparse.Namespace) -> None:
    state = _load_state(args.output)
    matrix = json.loads((args.output / "migration-matrix.json").read_text(encoding="utf-8"))
    if set(state.get("consumers", {})) != set(CONSUMER_SHAS):
        missing = sorted(set(CONSUMER_SHAS) - set(state.get("consumers", {})))
        raise RuntimeError(f"missing consumers: {missing}")
    for name in CONSUMER_SHAS:
        item = state["consumers"][name]
        if "baseline" not in item or "migrated" not in item:
            raise RuntimeError(f"consumer {name} is incomplete")
        if item["baseline"] != item["migrated"]:
            raise RuntimeError(f"consumer {name} changed test results")
        if item.get("policy") != 0 or item.get("import_linter") != 0:
            raise RuntimeError(f"consumer {name} failed policy/import acceptance")
        if item.get("residual_user_owned_legacy_references"):
            raise RuntimeError(f"consumer {name} retains legacy imports")
        managed = item.get("managed_surface")
        if not isinstance(managed, dict):
            raise RuntimeError(f"consumer {name} lacks managed-surface evidence")
        if managed.get("workflow_files") != ["ci.yml", "release.yml"]:
            raise RuntimeError(f"consumer {name} has an unexpected workflow set")
        if not managed.get("thin_ci_caller") or not managed.get("thin_release_caller"):
            raise RuntimeError(f"consumer {name} lacks thin Ternforge workflow callers")
        if managed.get("forbidden_legacy_references"):
            raise RuntimeError(f"consumer {name} retains forbidden legacy references")

    status_counts = Counter(item["status"] for item in matrix)
    if set(status_counts) - ALLOWED_DISPOSITIONS:
        raise RuntimeError(f"forbidden matrix states: {set(status_counts) - ALLOWED_DISPOSITIONS}")

    total = {
        "passed": sum(state["consumers"][name]["migrated"]["passed"] for name in CONSUMER_SHAS),
        "skipped": sum(state["consumers"][name]["migrated"]["skipped"] for name in CONSUMER_SHAS),
    }
    result = {
        "schema": state["schema"],
        "outcome": "passed",
        "revisions": state["revisions"],
        "capabilities": {"total": len(matrix), "dispositions": dict(status_counts), "unresolved": 0},
        "packages": state["packages"],
        "consumers": state["consumers"],
        "downstream_total": total,
        "migration_contract": {
            "compatibility_package": False,
            "dual_config_table": False,
            "atomic_consumer_migration": True,
            "managed_template_surface_replaced": True,
            "forbidden_legacy_references": 0,
            "policy_yaml_parser": "PyYAML",
        },
    }
    _write_json(args.output / "result.json", result)
    (args.output / "report.md").write_text(_report(state, matrix), encoding="utf-8")
    (args.output / "state.json").unlink(missing_ok=True)
    shutil.rmtree(args.output / "_work", ignore_errors=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "baseline", "migrate", "finalize"))
    parser.add_argument("--legacy", type=Path)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--testkit", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--assets", type=Path, default=Path(__file__).with_name("product-capability-parity"))
    parser.add_argument(
        "--template-candidate",
        type=Path,
        default=(
            Path(__file__).parents[1]
            / "evidence/template-system-hardening-20260801/renders/python-default"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--consumer", type=Path)
    parser.add_argument("--name")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    args.output = args.output.resolve()
    args.assets = args.assets.resolve()
    args.template_candidate = args.template_candidate.resolve()
    for attribute in ("legacy", "runtime", "policy", "testkit", "inventory", "consumer"):
        value = getattr(args, attribute)
        if value is not None:
            setattr(args, attribute, value.resolve())
    if args.phase == "prepare":
        required = ("legacy", "runtime", "policy", "testkit", "inventory")
        missing = [name for name in required if getattr(args, name) is None]
        if missing:
            raise ValueError(f"prepare requires: {', '.join('--' + name for name in missing)}")
        _prepare(args)
    elif args.phase == "baseline":
        _baseline(args)
    elif args.phase == "migrate":
        _migrate(args)
    else:
        _finalize(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
