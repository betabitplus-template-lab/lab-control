#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Any

UV_VERSION = "0.12.0"
PIP_AUDIT_VERSION = "2.10.1"
VULNERABLE_PACKAGE = "setuptools"
VULNERABLE_REQUIREMENT = "setuptools==65.5.0"


def run(
    *args: str,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        result.check_returncode()
    return result


def write_project(
    root: Path,
    *,
    name: str,
    runtime_dependencies: list[str],
    dev_dependencies: list[str],
) -> Path:
    project = root / name
    project.mkdir()
    runtime = json.dumps(runtime_dependencies)
    dev = json.dumps(dev_dependencies)
    (project / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                f'name = "{name}"',
                'version = "0.0.0"',
                'requires-python = ">=3.13"',
                f"dependencies = {runtime}",
                "",
                "[dependency-groups]",
                f"dev = {dev}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    run("uv", "lock", cwd=project)
    return project


def parse_json_output(result: subprocess.CompletedProcess[str]) -> Any:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"command did not return JSON: {result.args!r}\nstdout={result.stdout!r}\nstderr={result.stderr!r}"
        ) from error


def collect_vulnerability_ids(value: Any) -> list[str]:
    found: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key.lower() in {"id", "vulnerability_id", "vulnerability-id"}:
                    if isinstance(child, str) and child:
                        found.add(child)
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return sorted(found)


def contains_package(value: Any, package: str) -> bool:
    return package.lower() in json.dumps(value, sort_keys=True).lower()


def collect_vulnerable_packages(value: Any) -> list[str]:
    found: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            dependency = item.get("dependency")
            if isinstance(dependency, dict):
                name = dependency.get("name")
                if isinstance(name, str) and name:
                    found.add(name)
            name = item.get("name")
            vulns = item.get("vulns")
            if isinstance(name, str) and isinstance(vulns, list) and vulns:
                found.add(name)
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return sorted(found)


def command_record(
    result: subprocess.CompletedProcess[str], payload: Any | None = None
) -> dict[str, Any]:
    return {
        "command": list(result.args),
        "returncode": result.returncode,
        "stderr": result.stderr,
        "vulnerability_ids": collect_vulnerability_ids(payload),
        "vulnerable_packages": collect_vulnerable_packages(payload),
    }


def native_audit(project: Path, *, include_dev: bool, ignored: list[str] | None = None) -> tuple[subprocess.CompletedProcess[str], Any]:
    args = ["uv", "audit", "--frozen", "--output-format", "json"]
    if not include_dev:
        args.append("--no-dev")
    for vulnerability_id in ignored or []:
        args.extend(["--ignore", vulnerability_id])
    result = run(*args, cwd=project, check=False)
    return result, parse_json_output(result)


def export_runtime(project: Path) -> Path:
    output = project / "runtime-requirements.txt"
    run(
        "uv",
        "export",
        "--frozen",
        "--no-dev",
        "--no-emit-project",
        "--format",
        "requirements.txt",
        "--output-file",
        str(output),
        cwd=project,
    )
    return output


def pip_audit(
    tool_project: Path,
    requirements: Path,
    ignored: list[str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], Any]:
    args = [
        "uv",
        "run",
        "--frozen",
        "--no-sync",
        "pip-audit",
        "--requirement",
        str(requirements),
        "--no-deps",
        "--disable-pip",
        "--format",
        "json",
        "--progress-spinner",
        "off",
    ]
    for vulnerability_id in ignored or []:
        args.extend(["--ignore-vuln", vulnerability_id])
    result = run(*args, cwd=tool_project, check=False)
    return result, parse_json_output(result)


def render_report(result: dict[str, Any]) -> str:
    assertions = result["assertions"]
    rows = "\n".join(
        f"| `{name}` | {'PASS' if passed else 'FAIL'} |"
        for name, passed in assertions.items()
    )
    native_ids = ", ".join(result["observations"]["native_runtime_vulnerability_ids"])
    pip_ids = ", ".join(result["observations"]["pip_audit_runtime_vulnerability_ids"])
    return f"""# Locked dependency vulnerability audit lab

Date: 2026-07-31
Outcome: **{result['outcome']}**

## Question

Can a Python repository enforce a fail-closed vulnerability gate directly from its frozen `uv.lock`, limited to runtime dependencies, without product-specific Python tooling?

## Environment

- Python: `{result['environment']['python']}`
- Platform: `{result['environment']['platform']}`
- uv: `{result['environment']['uv']}`
- pip-audit: `{result['environment']['pip_audit']}`
- vulnerable fixture: `{VULNERABLE_REQUIREMENT}`

## Results

| Assertion | Result |
|---|---|
{rows}

Native `uv audit` vulnerability IDs: `{native_ids}`

`pip-audit` vulnerability IDs: `{pip_ids}`

## Conclusion

The production-ready path is the stable `pip-audit {PIP_AUDIT_VERSION}` CLI:

```bash
uv export --frozen --no-dev --no-emit-project --output-file runtime-requirements.txt
uv run --frozen --no-sync pip-audit --requirement runtime-requirements.txt --no-deps --disable-pip
```

It works as one ordinary development dependency plus direct CI commands. No custom production Python script or wrapper package is required.

Native `uv audit --frozen --no-dev` also enforces the gate correctly, but `uv {UV_VERSION}` still labels the command and its JSON schema experimental. It should be reconsidered after Astral stabilizes the interface.
"""


def perform_experiment() -> dict[str, Any]:
    actual_uv = run("uv", "--version").stdout.strip()
    if not actual_uv.startswith(f"uv {UV_VERSION} ") and actual_uv != f"uv {UV_VERSION}":
        raise RuntimeError(f"expected uv {UV_VERSION}, got {actual_uv}")

    with tempfile.TemporaryDirectory(prefix="locked-dependency-audit-") as temporary:
        root = Path(temporary)
        runtime_vulnerable = write_project(
            root,
            name="runtime-vulnerable",
            runtime_dependencies=[VULNERABLE_REQUIREMENT],
            dev_dependencies=[f"pip-audit=={PIP_AUDIT_VERSION}"],
        )
        dev_only_vulnerable = write_project(
            root,
            name="dev-only-vulnerable",
            runtime_dependencies=[],
            dev_dependencies=[VULNERABLE_REQUIREMENT],
        )

        run("uv", "sync", "--locked", "--all-groups", cwd=runtime_vulnerable)
        actual_pip_audit = run(
            "uv",
            "run",
            "--frozen",
            "--no-sync",
            "pip-audit",
            "--version",
            cwd=runtime_vulnerable,
        ).stdout.strip()

        native_runtime, native_runtime_payload = native_audit(
            runtime_vulnerable,
            include_dev=False,
        )
        native_runtime_ids = collect_vulnerability_ids(native_runtime_payload)

        native_dev_excluded, native_dev_excluded_payload = native_audit(
            dev_only_vulnerable,
            include_dev=False,
        )
        native_dev_included, native_dev_included_payload = native_audit(
            dev_only_vulnerable,
            include_dev=True,
        )
        native_ignored, native_ignored_payload = native_audit(
            runtime_vulnerable,
            include_dev=False,
            ignored=native_runtime_ids,
        )

        runtime_requirements = export_runtime(runtime_vulnerable)
        dev_only_runtime_requirements = export_runtime(dev_only_vulnerable)

        pip_runtime, pip_runtime_payload = pip_audit(
            runtime_vulnerable,
            runtime_requirements,
        )
        pip_runtime_ids = collect_vulnerability_ids(pip_runtime_payload)
        pip_dev_excluded, pip_dev_excluded_payload = pip_audit(
            runtime_vulnerable,
            dev_only_runtime_requirements,
        )
        pip_ignored, pip_ignored_payload = pip_audit(
            runtime_vulnerable,
            runtime_requirements,
            ignored=pip_runtime_ids,
        )

        assertions = {
            "native_runtime_vulnerability_blocks": (
                native_runtime.returncode == 1
                and bool(native_runtime_ids)
                and contains_package(native_runtime_payload, VULNERABLE_PACKAGE)
            ),
            "native_no_dev_excludes_dev_only_vulnerability": (
                native_dev_excluded.returncode == 0
                and not collect_vulnerability_ids(native_dev_excluded_payload)
            ),
            "native_default_includes_dev_vulnerability": (
                native_dev_included.returncode == 1
                and bool(collect_vulnerability_ids(native_dev_included_payload))
                and contains_package(native_dev_included_payload, VULNERABLE_PACKAGE)
            ),
            "native_exact_ignore_restores_success": (
                bool(native_runtime_ids)
                and native_ignored.returncode == 0
                and not collect_vulnerability_ids(native_ignored_payload)
            ),
            "native_command_is_still_experimental": (
                "`uv audit` is experimental" in native_runtime.stderr
                and "schema may change" in native_runtime.stderr
            ),
            "pip_audit_exported_runtime_vulnerability_blocks": (
                pip_runtime.returncode == 1
                and bool(pip_runtime_ids)
                and contains_package(pip_runtime_payload, VULNERABLE_PACKAGE)
            ),
            "pip_audit_export_excludes_dev_only_vulnerability": (
                pip_dev_excluded.returncode == 0
                and not collect_vulnerability_ids(pip_dev_excluded_payload)
            ),
            "pip_audit_exact_ignore_restores_success": (
                bool(pip_runtime_ids)
                and pip_ignored.returncode == 0
                and not collect_vulnerability_ids(pip_ignored_payload)
            ),
            "pip_audit_runs_from_locked_dev_environment": (
                actual_pip_audit == f"pip-audit {PIP_AUDIT_VERSION}"
                and (runtime_vulnerable / ".venv").is_dir()
            ),
            "runtime_export_is_fully_pinned": (
                VULNERABLE_REQUIREMENT
                in runtime_requirements.read_text(encoding="utf-8")
                and VULNERABLE_PACKAGE
                not in dev_only_runtime_requirements.read_text(encoding="utf-8")
            ),
        }

        result = {
            "question": (
                "Can a Python repository enforce a fail-closed known-vulnerability gate "
                "from a frozen uv.lock, limited to runtime dependencies, without custom tooling?"
            ),
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "uv": actual_uv,
                "pip_audit": actual_pip_audit,
            },
            "fixtures": {
                "runtime_vulnerable": VULNERABLE_REQUIREMENT,
                "dev_only_vulnerable": VULNERABLE_REQUIREMENT,
            },
            "observations": {
                "native_runtime_vulnerability_ids": native_runtime_ids,
                "pip_audit_runtime_vulnerability_ids": pip_runtime_ids,
                "runtime_requirements": runtime_requirements.read_text(encoding="utf-8"),
                "dev_only_runtime_requirements": dev_only_runtime_requirements.read_text(
                    encoding="utf-8"
                ),
            },
            "commands": {
                "native_runtime": command_record(native_runtime, native_runtime_payload),
                "native_dev_excluded": command_record(
                    native_dev_excluded, native_dev_excluded_payload
                ),
                "native_dev_included": command_record(
                    native_dev_included, native_dev_included_payload
                ),
                "native_ignored": command_record(native_ignored, native_ignored_payload),
                "pip_runtime": command_record(pip_runtime, pip_runtime_payload),
                "pip_dev_excluded": command_record(
                    pip_dev_excluded, pip_dev_excluded_payload
                ),
                "pip_ignored": command_record(pip_ignored, pip_ignored_payload),
            },
            "assertions": assertions,
            "outcome": "passed" if all(assertions.values()) else "failed",
            "conclusion": (
                f"pip-audit {PIP_AUDIT_VERSION} provides the production-ready frozen runtime "
                f"dependency gate. uv {UV_VERSION} also works, but its audit command remains "
                "experimental."
            ),
        }
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-report", type=Path)
    args = parser.parse_args()

    result = perform_experiment()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    report = render_report(result)

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered, encoding="utf-8")
    if args.output_report is not None:
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "outcome": result["outcome"],
                "environment": result["environment"],
                "observations": result["observations"],
                "assertions": result["assertions"],
                "conclusion": result["conclusion"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    raise SystemExit(0 if result["outcome"] == "passed" else 1)


if __name__ == "__main__":
    main()
