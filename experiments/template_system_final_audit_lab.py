#!/usr/bin/env python3
"""Audit the remaining Ternforge template-system contract invariants.

This follow-up does not rebuild the full Python product. EXP-0033 already does
that on Ubuntu. It verifies that the committed hardening evidence is internally
consistent, that component source paths are question-independent, and that the
cross-platform Copier matrix covers the new-executable file-mode edge case.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

import yaml

COPIER_VERSION = "9.17.0"
UV_VERSION = "0.12.0"
PYTHON_VERSION = "3.13"

INFRA_INCLUDE_PATHS = (
    "components/agents/base/**/*",
    "components/repository/base/**/*",
    "components/repository/copier/**/*",
)

PYTHON_INCLUDE_PATHS = (
    "components/agents/base/**/*",
    "components/agents/py-library/**/*",
    "components/repository/base/template/.editorconfig",
    "components/repository/base/template/LICENSE",
    "components/repository/copier/**/*",
    "components/project/py/base/**/*",
    "components/project/py/library/**/*",
    "components/quality/py/**/*",
    "components/delivery/updates/**/*",
    "components/delivery/ci/py-library/**/*",
    "components/delivery/release/library/**/*",
)

FORBIDDEN_PATH_TOKENS = ("[[[", "[[%", "[[#", "{{", "{%", "{#")
INCLUDE_PATTERN = re.compile(
    r'\[\[%\s*include\s+"template/_components/([^"\n]+)"\s*%\]\]'
)
ACTION_PATTERN = re.compile(r"^\s*uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE)
FULL_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def run(command: Sequence[str], *, cwd: Path) -> str:
    process = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"command failed ({process.returncode}): {' '.join(command)}\n"
            f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return process.stdout.strip()


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object in {path}")
    return value


def validate_component_source_paths(component_root: Path) -> int:
    count = 0
    violations: list[str] = []
    for path in sorted(component_root.rglob("*")):
        relative = path.relative_to(component_root).as_posix()
        count += 1
        if any(token in relative for token in FORBIDDEN_PATH_TOKENS):
            violations.append(relative)
    if violations:
        raise RuntimeError(
            "component source paths depend on template questions: "
            + ", ".join(violations)
        )
    return count


def validate_negative_path_fixture() -> None:
    with tempfile.TemporaryDirectory(prefix="component-path-negative-") as directory:
        root = Path(directory)
        bad = root / "components/project/py/template/src/[[[ package_name ]]]/bad.py"
        bad.parent.mkdir(parents=True)
        bad.write_text("BAD = True\n", encoding="utf-8")
        try:
            validate_component_source_paths(root)
        except RuntimeError as error:
            if "depend on template questions" not in str(error):
                raise
        else:
            raise RuntimeError(
                "component path validator missed a templated source path"
            )


def vendir_content(view_root: Path) -> dict[str, object]:
    data = yaml.safe_load((view_root / "vendir.yml").read_text(encoding="utf-8"))
    return data["directories"][0]["contents"][0]


def validate_vendir_view(view_root: Path, include_paths: Sequence[str]) -> None:
    content = vendir_content(view_root)
    expected_includes = list(include_paths)
    if content.get("includePaths") != expected_includes:
        raise RuntimeError(f"unexpected includePaths in {view_root}")
    if content.get("excludePaths") != [".git", ".git/**/*"]:
        raise RuntimeError(f"unexpected excludePaths in {view_root}")
    if content.get("legalPaths") != []:
        raise RuntimeError(f"legalPaths must be explicitly empty in {view_root}")
    if "newRootPath" in content:
        raise RuntimeError(f"newRootPath is not allowed in {view_root}")


def wrapper_targets(view_root: Path) -> set[str]:
    targets: set[str] = set()
    for path in sorted(view_root.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        targets.update(INCLUDE_PATTERN.findall(text))
    if not targets:
        raise RuntimeError(f"no component wrapper targets found in {view_root}")
    return targets


def selected_component_files(
    component_root: Path, include_paths: Sequence[str]
) -> set[str]:
    selected: set[str] = set()
    for include_path in include_paths:
        if include_path.endswith("/**/*"):
            prefix = include_path.removesuffix("/**/*")
            source = component_root / prefix
            if not source.is_dir():
                raise RuntimeError(
                    f"declared component directory does not exist: {prefix}"
                )
            selected.update(
                path.relative_to(component_root).as_posix()
                for path in source.rglob("*")
                if path.is_file()
            )
            continue
        source = component_root / include_path
        if not source.is_file():
            raise RuntimeError(
                f"declared component file does not exist: {include_path}"
            )
        selected.add(include_path)
    return selected


def validate_wrapper_targets(
    component_root: Path, view_root: Path, include_paths: Sequence[str]
) -> int:
    targets = wrapper_targets(view_root)
    selected = selected_component_files(component_root, include_paths)
    for target in sorted(targets):
        if any(token in target for token in FORBIDDEN_PATH_TOKENS):
            raise RuntimeError(f"wrapper target is not stable: {target}")
        if not (component_root / target).is_file():
            raise RuntimeError(f"wrapper target does not exist: {target}")
    if selected != targets:
        raise RuntimeError(
            f"selected component snapshot does not exactly match wrappers in "
            f"{view_root}: unused={sorted(selected - targets)}, "
            f"missing={sorted(targets - selected)}"
        )
    return len(targets)


def validate_action_pins(repository_root: Path) -> int:
    workflow_paths = (
        repository_root / ".github/workflows/python-template-product-parity-lab.yml",
        repository_root / ".github/workflows/template-system-integration-lab.yml",
        repository_root / ".github/workflows/template-system-hardening-lab.yml",
        repository_root / ".github/workflows/template-system-final-audit-lab.yml",
        repository_root / ".github/workflows/copier-matrix.yml",
    )
    count = 0
    for workflow in workflow_paths:
        text = workflow.read_text(encoding="utf-8")
        for owner_path, reference in ACTION_PATTERN.findall(text):
            if owner_path.startswith("./"):
                continue
            count += 1
            if not FULL_SHA_PATTERN.fullmatch(reference):
                raise RuntimeError(
                    f"workflow action is not pinned to a full SHA: "
                    f"{workflow}:{owner_path}@{reference}"
                )
    if count == 0:
        raise RuntimeError("no external workflow actions were audited")
    return count


def validate_matrix(matrix: dict[str, object]) -> None:
    if matrix.get("failures") != []:
        raise RuntimeError(f"Copier matrix failures: {matrix.get('failures')}")
    if matrix.get("copier_version") != f"copier {COPIER_VERSION}":
        raise RuntimeError("Copier matrix used an unexpected Copier version")
    if matrix.get("python_version") != PYTHON_VERSION:
        raise RuntimeError("Copier matrix used an unexpected Python version")
    if matrix.get("new_executable_index_mode") != "100755":
        raise RuntimeError("controlled new executable was not recorded as 100755")
    if matrix.get("file_mode_false_new_executable_index_mode") != "100644":
        raise RuntimeError("core.fileMode=false negative control did not record 100644")
    for name in (
        "controlled_new_executable_mode",
        "file_mode_false_negative_control",
        "executable_bit_update",
        "clean_update",
        "true_conflict_markers",
        "required_question_without_default_fails",
    ):
        if matrix.get(name) is not True:
            raise RuntimeError(f"Copier matrix check failed: {name}")


def validate_hardening_result(result: dict[str, object]) -> None:
    checks = result.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise RuntimeError("hardening result has no checks")
    failures = [name for name, passed in checks.items() if passed is not True]
    if failures:
        raise RuntimeError(f"hardening evidence contains failed checks: {failures}")
    versions = result.get("versions")
    if not isinstance(versions, dict):
        raise RuntimeError("hardening result has no versions")
    expected = {"copier": COPIER_VERSION, "uv": UV_VERSION, "vendir": "0.46.0"}
    for key, value in expected.items():
        if versions.get(key) != value:
            raise RuntimeError(f"hardening {key} version mismatch")
    if result.get("infra_component_snapshot_file_count") != 15:
        raise RuntimeError("unexpected infra snapshot size")
    if result.get("python_component_snapshot_file_count") != 166:
        raise RuntimeError("unexpected Python snapshot size")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hardening-evidence", type=Path, required=True)
    parser.add_argument("--matrix-result", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repository_root = Path(__file__).resolve().parents[1]
    hardening = args.hardening_evidence.resolve()
    component_root = hardening / "components"
    infra_view = hardening / "template-views/infra-repository"
    python_view = hardening / "template-views/python-library"

    actual_python = f"{sys.version_info.major}.{sys.version_info.minor}"
    if actual_python != PYTHON_VERSION:
        raise RuntimeError(f"expected Python {PYTHON_VERSION}, got {actual_python}")
    actual_copier = run(["copier", "--version"], cwd=repository_root)
    if actual_copier != f"copier {COPIER_VERSION}":
        raise RuntimeError(f"expected Copier {COPIER_VERSION}, got {actual_copier}")
    actual_uv = run(["uv", "--version"], cwd=repository_root).split()[1]
    if actual_uv != UV_VERSION:
        raise RuntimeError(f"expected uv {UV_VERSION}, got {actual_uv}")

    component_path_count = validate_component_source_paths(component_root)
    validate_negative_path_fixture()
    validate_vendir_view(infra_view, INFRA_INCLUDE_PATHS)
    validate_vendir_view(python_view, PYTHON_INCLUDE_PATHS)

    if (
        not (component_root / "LICENSE").is_file()
        or not (component_root / "NOTICE").is_file()
    ):
        raise RuntimeError("hardening legal-path sentinels are missing")
    explicit_product_license = "components/repository/base/template/LICENSE"
    if not (component_root / explicit_product_license).is_file():
        raise RuntimeError("explicit product LICENSE component is missing")

    infra_target_count = validate_wrapper_targets(
        component_root, infra_view, INFRA_INCLUDE_PATHS
    )
    python_target_count = validate_wrapper_targets(
        component_root, python_view, PYTHON_INCLUDE_PATHS
    )
    if explicit_product_license not in wrapper_targets(infra_view):
        raise RuntimeError("infra template does not explicitly select product LICENSE")
    if explicit_product_license not in wrapper_targets(python_view):
        raise RuntimeError("Python template does not explicitly select product LICENSE")

    action_pin_count = validate_action_pins(repository_root)
    matrix = load_json(args.matrix_result.resolve())
    validate_matrix(matrix)
    hardening_result = load_json(hardening / "result.json")
    validate_hardening_result(hardening_result)

    matrix_workflow = (
        repository_root / ".github/workflows/copier-matrix.yml"
    ).read_text(encoding="utf-8")
    if "github.event_name != 'pull_request'" not in matrix_workflow:
        raise RuntimeError(
            "Copier matrix still exposes the write-capable App token to PRs"
        )
    matrix_source = (repository_root / "acceptance/copier_matrix.py").read_text(
        encoding="utf-8"
    )
    for required in (
        '"core.fileMode", "true"',
        '"core.fileMode", "false"',
        "scripts/new-managed-tool.sh",
    ):
        if required not in matrix_source:
            raise RuntimeError(
                f"Copier matrix is missing controlled mode logic: {required}"
            )

    checks = {
        "actual_tool_versions_exact": True,
        "component_source_paths_stable": True,
        "component_path_negative_fixture_detected": True,
        "vendir_selection_contract_exact": True,
        "wrapper_targets_exist_and_are_declared": True,
        "selected_snapshots_match_wrappers_exactly": True,
        "legal_files_explicitly_owned": True,
        "cited_workflow_actions_immutable": True,
        "pull_request_token_boundary": True,
        "cross_platform_new_executable_matrix": True,
        "hardening_evidence_consistent": True,
    }
    result = {
        "status": "passed",
        "versions": {
            "python": PYTHON_VERSION,
            "copier": COPIER_VERSION,
            "uv": UV_VERSION,
            "vendir": "0.46.0",
        },
        "checks": checks,
        "component_path_count": component_path_count,
        "infra_wrapper_target_count": infra_target_count,
        "python_wrapper_target_count": python_target_count,
        "action_pin_count": action_pin_count,
        "matrix_modes": {
            "controlled": matrix["new_executable_index_mode"],
            "core_file_mode_false": matrix["file_mode_false_new_executable_index_mode"],
        },
    }

    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        for path in sorted(output_dir.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
    output_dir.mkdir(parents=True, exist_ok=True)
    write(
        output_dir / "result.json", json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    report = f"""# Template-system final audit

Status: **PASS**

This follow-up keeps the EXP-0033 boundary precise: the complete hardened
product run is an Ubuntu acceptance result; the controlled Copier lifecycle and
new-executable mode checks run on both Ubuntu and macOS.

```text
component paths audited       {component_path_count}
infra wrapper targets         {infra_target_count}
Python wrapper targets        {python_target_count}
immutable action pins         {action_pin_count}
controlled new file mode      {matrix["new_executable_index_mode"]}
fileMode=false control        {matrix["file_mode_false_new_executable_index_mode"]}
```

Validated:

* component source paths contain no final-template question syntax;
* a negative templated-path fixture is rejected;
* Vendir `includePaths`, `excludePaths`, `legalPaths: []` and no-`newRootPath`
  contracts are exact;
* all final-template wrapper targets exist and belong to declared components;
* each selected component snapshot equals its wrapper-target set exactly;
* product LICENSE output is explicitly selected while repository-root legal
  sentinels remain selection tests rather than implicit product files;
* workflows cited by the current template-system evidence use full action SHAs;
* pull-request matrix runs do not mint the write-capable lab App token;
* `core.fileMode=false` reproduces `100644`, while the controlled preflight
  records the new executable as `100755`;
* actual Python, Copier and uv versions match the documented exact contract.
"""
    write(output_dir / "report.md", report)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
