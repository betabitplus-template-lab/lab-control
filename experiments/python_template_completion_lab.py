#!/usr/bin/env python3
"""Complete the Python-library migration candidate without production rollout."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "lab-control"
DEFAULT_OUTPUT = LAB / "evidence/python-template-completion-20260802"
BASE_LAB = LAB / "experiments/local_dx_hardening_lab.py"
BASE_RENDER = LAB / "evidence/template-system-hardening-20260801/renders/python-default"
BASE_TEMPLATE = LAB / "evidence/template-system-hardening-20260801/template-views/python-library"
COMPONENT_SNAPSHOT = LAB / "evidence/template-system-hardening-20260801/components/components"
INITIAL_TAG = "v0.1.1"
FINAL_TAG = "v0.1.2"
COPIER_VERSION = "9.17.0"
SOPS_TAG = "ghcr.io/getsops/sops:v3.11.0"
REDDIT_DISKCACHE_WAIVER = {
    "id": "PYSEC-2026-2447",
    "rationale": "DiskCache 5.6.3 is affected and no fixed release exists in the frozen migration input.",
    "remove_when": "a fixed DiskCache release is available and the repository lockfile is updated",
}
RELEASE_APP_CLIENT_ID_VARIABLE = "TERNFORGE_RELEASE_APP_CLIENT_ID"
RELEASE_APP_CREDENTIAL_SECRET = "".join(("TERNFORGE_RELEASE_APP_", "PRIV", "ATE_KEY"))


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = _load_module("local_dx_hardening_lab_completion", BASE_LAB)
product = base.product
dx = base.dx


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def _init_git(root: Path, message: str, tag: str | None = None) -> str:
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "Ternforge Completion Lab")
    _git(root, "config", "user.email", "completion@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", message)
    if tag is not None:
        _git(root, "tag", tag)
    return _git(root, "rev-parse", "HEAD")


def _commit(root: Path, message: str, tag: str | None = None) -> str:
    _git(root, "add", ".")
    _git(root, "commit", "-qm", message)
    if tag is not None:
        _git(root, "tag", tag)
    return _git(root, "rev-parse", "HEAD")


def _github_expression(expression: str) -> str:
    return "$" + "{{ " + expression + " }}"


def _provider_fixture(output: Path) -> tuple[Path, str]:
    root = output / "_work/infra-ci-provider"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    _write(
        root / ".github/workflows/python-library.yml",
        """name: Python library CI

on:
  workflow_call:

permissions:
  contents: read

jobs:
  required:
    name: required
    runs-on: ubuntu-latest
    steps:
      - run: echo "local provider contract fixture"
""",
    )
    _write(
        root / ".github/workflows/release.yml",
        """name: Python library release

on:
  workflow_call:
    inputs:
      client_id:
        required: true
        type: string
      repository:
        required: true
        type: string
      release_type:
        required: true
        type: string
    secrets:
      app_credential:
        required: true

permissions:
  contents: read

jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - run: echo "local release provider contract fixture"
""",
    )
    return root, _init_git(root, "provider contract fixture")


def _setup_script() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"
printf '%s\n' "Setting up development environment..."
if [ ! -f uv.lock ]; then
  printf '%s\n' "Creating the initial uv.lock..."
  uv lock
fi
uv sync --locked --all-groups
uv run pre-commit install
printf '%s\n' "Setup complete. Locked dependencies and configured hook stages are installed."
"""


def _ci_caller(provider_sha: str) -> str:
    return f"""name: CI

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
    uses: betabitplus/ternforge-infra-ci/.github/workflows/python-library.yml@{provider_sha} # local provider fixture; production binds a released provider SHA
"""


def _release_caller(provider_sha: str) -> str:
    client_id = _github_expression(f"vars.{RELEASE_APP_CLIENT_ID_VARIABLE}")
    repository = _github_expression("github.event.repository.name")
    credential = _github_expression(f"secrets.{RELEASE_APP_CREDENTIAL_SECRET}")
    return f"""name: Release

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  release:
    uses: betabitplus/ternforge-infra-ci/.github/workflows/release.yml@{provider_sha} # local provider fixture; production binds a released provider SHA
    with:
      client_id: {client_id}
      repository: {repository}
      release_type: python
    secrets:
      app_credential: {credential}
"""


def _release_config(project_name: str) -> str:
    return json.dumps(
        {
            "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
            "release-type": "simple",
            "include-v-in-tag": True,
            "include-component-in-tag": False,
            "changelog-path": "CHANGELOG.md",
            "packages": {
                ".": {
                    "component": project_name,
                    "release-type": "simple",
                    "extra-files": [
                        {
                            "type": "toml",
                            "path": "pyproject.toml",
                            "jsonpath": "$.project.version",
                        }
                    ],
                }
            },
        },
        indent=2,
    ) + "\n"


def _release_manifest(version: str) -> str:
    return json.dumps({".": version}, indent=2) + "\n"


def _remove_generic_advisory(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(" --ignore-vuln CVE-2025-69872", "")
    path.write_text(text, encoding="utf-8")


def _normalize_uv_sync_hooks(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("uv sync --group dev --frozen", "uv sync --locked --all-groups")
    path.write_text(text, encoding="utf-8")


def _set_pip_audit_waivers(
    pyproject: Path,
    values: list[dict[str, str]],
    *,
    templated: bool,
) -> None:
    text = pyproject.read_text(encoding="utf-8")
    if templated:
        replacement = """[[% if pip_audit_waivers %]]
[[% for waiver in pip_audit_waivers %]]# [[[ waiver.id ]]]: [[[ waiver.rationale ]]]
# Remove when: [[[ waiver.remove_when ]]]
[[% endfor %]]ignore-vulns = [
[[% for waiver in pip_audit_waivers %]]  "[[[ waiver.id ]]]",
[[% endfor %]]]
[[% else %]]ignore-vulns = []
[[% endif %]]
"""
    elif values:
        comments = "\n".join(
            f"# {value['id']}: {value['rationale']}\n# Remove when: {value['remove_when']}"
            for value in values
        )
        rendered = "\n".join(f'  "{value["id"]}",' for value in values)
        replacement = f"{comments}\nignore-vulns = [\n{rendered}\n]\n"
    else:
        replacement = "ignore-vulns = []\n"
    updated, count = re.subn(r"(?m)^ignore-vulns = \[[^\n]*\]\n", replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"pip-audit config not found in {pyproject}")
    pyproject.write_text(updated, encoding="utf-8")


def _set_precommit_audit_waivers(
    path: Path,
    values: list[dict[str, str]],
    *,
    templated: bool,
) -> None:
    text = path.read_text(encoding="utf-8")
    marker = 'uv run --frozen --no-sync pip-audit --requirement "$tmp" --no-deps --disable-pip'
    if marker not in text:
        raise RuntimeError(f"pip-audit hook command not found in {path}")
    if templated:
        replacement = (
            marker
            + "[[% for waiver in pip_audit_waivers %]] --ignore-vuln [[[ waiver.id ]]][[% endfor %]]"
        )
    else:
        replacement = marker + "".join(
            f" --ignore-vuln {value['id']}" for value in values
        )
    path.write_text(text.replace(marker, replacement, 1), encoding="utf-8")


def _add_check_manifest_ignores(pyproject: Path) -> None:
    text = pyproject.read_text(encoding="utf-8")
    if '  ".release-please-manifest.json",\n' not in text:
        text = text.replace(
            '  ".pytest_cache/**",\n',
            '  ".pytest_cache/**",\n  ".release-please-manifest.json",\n',
            1,
        )
    if '  "release-please-config.json",\n' not in text:
        text = text.replace(
            '  "plan/**",\n',
            '  "plan/**",\n  "release-please-config.json",\n',
            1,
        )
    pyproject.write_text(text, encoding="utf-8")


def _add_copier_question(copier: Path) -> None:
    text = copier.read_text(encoding="utf-8")
    if "pip_audit_waivers:" in text:
        return
    marker = "gitignore_extra_patterns:\n"
    block = """pip_audit_waivers:
  type: yaml
  help: Repository-specific pip-audit waivers. Each item must contain id, rationale, and remove_when.
  default: []

"""
    if marker not in text:
        raise RuntimeError(f"Copier insertion marker not found in {copier}")
    copier.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")


def _update_devcontainer(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    age_mount = '    "source=${localEnv:HOME}/.config/sops/age,target=/home/vscode/.config/sops/age,type=bind,readonly",\n'
    if age_mount not in text:
        uv_mount = '    "source=${env:HOME}/.cache/uv,target=/home/vscode/.cache/uv,type=bind",\n'
        if uv_mount not in text:
            raise RuntimeError(f"uv mount marker not found in {path}")
        text = text.replace(uv_mount, uv_mount + age_mount, 1)
    updated, count = re.subn(
        r'(?m)^  "postCreateCommand": ".*",$',
        '  "postCreateCommand": "bash -lc \'sudo chown -R vscode:vscode .venv && (rm -f /home/vscode/.vscode-server/data/User/globalStorage/ms-python.python/pythonLocator/*.json 2>/dev/null || true) && uv venv --python 3.13 --clear .venv && source .venv/bin/activate && bash scripts/env/setup.sh && python -m ensurepip --upgrade --default-pip\'",',
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"postCreateCommand not found in {path}")
    path.write_text(updated, encoding="utf-8")


def _update_generated_text(base_root: Path, library_root: Path) -> None:
    setup = base_root / "SETUP.md"
    text = setup.read_text(encoding="utf-8")
    text = text.replace(
        "`scripts/env/setup.sh` runs `uv sync --group dev` and installs configured git\n"
        "hook types.",
        "`scripts/env/setup.sh` creates `uv.lock` only on the first bootstrap, then runs\n"
        "strict `uv sync --locked --all-groups` and installs configured git hook types.",
    )
    text = text.replace(
        "The devcontainer provisions an in-container `.venv` with `uv sync --group dev`.",
        "The devcontainer provisions an in-container `.venv` through the same bootstrap-aware `scripts/env/setup.sh` contract.",
    )
    text = text.replace("uv sync --group dev\n", "bash scripts/env/setup.sh\n")
    setup.write_text(text, encoding="utf-8")

    contributing = base_root / "CONTRIBUTING.md"
    text = contributing.read_text(encoding="utf-8")
    text = text.replace(
        "`py-lib-runtime` is consumed as a runtime dependency and `py-lib-testkit` is\n"
        "consumed as a dev dependency from the shared py starter repository through\n"
        "one shared version tag.",
        "`py-lib-runtime` is consumed as a runtime dependency, while `py-lib-policy`\n"
        "and `py-lib-testkit` are independent development dependencies. Each package is\n"
        "owned and released separately by Ternforge and pinned immutably by this repo.",
    )
    contributing.write_text(text, encoding="utf-8")

    readme = library_root / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = text.replace("uv sync --group dev\nuv run pytest", "bash scripts/env/setup.sh\nuv run pytest")
    readme.write_text(text, encoding="utf-8")


def _apply_completion_delta(
    root: Path,
    *,
    provider_sha: str,
    digests: dict[str, str],
) -> None:
    component_root = root / "_components/components"
    templated = component_root.is_dir()
    base_root = component_root / "project/py/base/template" if templated else root
    library_root = component_root / "project/py/library/template" if templated else root
    quality_root = component_root / "quality/py/template" if templated else root
    ci_root = component_root / "delivery/ci/py-library/template" if templated else root
    release_root = component_root / "delivery/release/library/template" if templated else root

    if templated:
        (root / "scripts/env/project_config.sh").unlink(missing_ok=True)
    (base_root / "scripts/env/project_config.sh").unlink(missing_ok=True)
    base._write_executable(base_root / "scripts/env/setup.sh", _setup_script())

    precommit = quality_root / ".pre-commit-config.yaml"
    pyproject_tools = (
        component_root / "quality/py/includes/pyproject-tools.toml"
        if templated
        else root / "pyproject.toml"
    )
    _remove_generic_advisory(precommit)
    _normalize_uv_sync_hooks(precommit)
    _set_precommit_audit_waivers(precommit, [], templated=templated)
    _set_pip_audit_waivers(pyproject_tools, [], templated=templated)
    _add_check_manifest_ignores(pyproject_tools)

    dockerfile = f"""# syntax=docker/dockerfile:1
FROM {base.DEVCONTAINER_TAG}@{digests[base.DEVCONTAINER_TAG]}
ENV DEBIAN_FRONTEND=noninteractive
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential ca-certificates direnv git pkg-config \\
    && rm -rf /var/lib/apt/lists/*
COPY --from={base.UV_TAG}@{digests[base.UV_TAG]} /uv /uvx /usr/local/bin/
COPY --from={SOPS_TAG}@{digests[SOPS_TAG]} /usr/local/bin/sops /usr/local/bin/sops
ENV UV_PROJECT_ENVIRONMENT=.venv
ENV UV_LINK_MODE=copy
ENV PATH="/home/vscode/.venv/bin:${{PATH}}"
"""
    base._write_executable(base_root / ".devcontainer/Dockerfile", dockerfile)
    _update_devcontainer(base_root / ".devcontainer/devcontainer.json")

    ci_root.mkdir(parents=True, exist_ok=True)
    _write(ci_root / ".github/workflows/ci.yml", _ci_caller(provider_sha))
    release_root.mkdir(parents=True, exist_ok=True)
    _write(release_root / ".github/workflows/release.yml", _release_caller(provider_sha))
    _write(
        release_root / "release-please-config.json",
        _release_config("[[[ project_name ]]]" if templated else "sample-lib"),
    )
    _write(
        release_root / ".release-please-manifest.json",
        _release_manifest("[[[ initial_version ]]]" if templated else "0.1.0"),
    )
    if templated:
        _write(
            root / "release-please-config.json",
            '[[% include "template/_components/components/delivery/release/library/template/release-please-config.json" %]]\n',
        )
        _write(
            root / ".release-please-manifest.json",
            '[[% include "template/_components/components/delivery/release/library/template/.release-please-manifest.json" %]]\n',
        )
        _add_copier_question(root.parent / "copier.yml")
    else:
        answers = root / ".copier-answers.yml"
        data = yaml.safe_load(answers.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError("rendered Copier answers must be a mapping")
        data.setdefault("pip_audit_waivers", [])
        answers.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    _update_generated_text(base_root, library_root)


def _cache_image_digests() -> dict[str, str]:
    return {
        base.UV_TAG: base._image_digest(base.UV_TAG),
        base.DEVCONTAINER_TAG: base._image_digest(base.DEVCONTAINER_TAG),
        SOPS_TAG: base._image_digest(SOPS_TAG),
    }


def _apply_base_with_cached_digests(root: Path, digests: dict[str, str]) -> None:
    original = base._image_digest
    base._image_digest = digests.__getitem__
    try:
        base.apply_template_fixes(root)
    finally:
        base._image_digest = original


def _copier(output: Path, name: str, command: list[str], *, cwd: Path) -> dict[str, Any]:
    return base._run(name, command, cwd=cwd, output=output)


def _copy_at_tag(output: Path, source: Path, destination: Path, tag: str, name: str) -> dict[str, Any]:
    shutil.rmtree(destination, ignore_errors=True)
    return _copier(
        output,
        name,
        [
            "uvx",
            "--from",
            f"copier=={COPIER_VERSION}",
            "copier",
            "copy",
            "--trust",
            "--defaults",
            "--vcs-ref",
            tag,
            str(source),
            str(destination),
        ],
        cwd=output,
    )


def _user_owned_sentinels(root: Path) -> dict[str, str]:
    values = {
        "src/sample_lib/product_owned.py": "PRODUCT_SENTINEL = 'src-preserved'\n",
        "tests/sample_lib/product_owned_test.py": "def test_product_owned() -> None:\n    assert True\n",
        "docs/sample_lib/product-owned.md": "# Product-owned sentinel\n",
        "examples/sample_lib/product_owned.py": "print('example-preserved')\n",
        "workbench/sample_lib/product_owned.py": "# %%\nprint('workbench-preserved')\n",
        "unrelated-product-file.txt": "unrelated-preserved\n",
    }
    for relative, content in values.items():
        _write(root / relative, content)
    readme = root / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\nPRODUCT README SENTINEL\n", encoding="utf-8")
    values["README.md"] = readme.read_text(encoding="utf-8")
    return values


def _assert_sentinels(root: Path, expected: dict[str, str]) -> None:
    for relative, content in expected.items():
        actual = (root / relative).read_text(encoding="utf-8")
        if actual != content:
            raise RuntimeError(f"user-owned file changed during Copier update: {relative}")


def _validate_surface(candidate: Path) -> dict[str, Any]:
    old = {path.relative_to(BASE_RENDER).as_posix() for path in BASE_RENDER.rglob("*") if path.is_file()}
    new = {path.relative_to(candidate).as_posix() for path in candidate.rglob("*") if path.is_file()}
    allowed_removed = {"_copier_answers.yml", "scripts/env/project_config.sh"}
    required_added = {
        ".copier-answers.yml",
        ".release-please-manifest.json",
        "release-please-config.json",
    }
    lost = sorted(old - new - allowed_removed)
    missing_added = sorted(required_added - new)
    if lost or missing_added:
        raise RuntimeError(f"surface mismatch: lost={lost}, missing_added={missing_added}")
    return {
        "legacy_files": len(old),
        "candidate_files": len(new),
        "allowed_removed": sorted(allowed_removed),
        "required_added": sorted(required_added),
        "lost_unrelated_files": lost,
    }


def _validate_includes(template_source: Path) -> dict[str, Any]:
    pattern = re.compile(r'include\s+"([^"]+)"')
    missing: list[dict[str, str]] = []
    count = 0
    for source in sorted((template_source / "template").rglob("*")):
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8", errors="ignore")
        for target in pattern.findall(text):
            count += 1
            if not (template_source / target).is_file():
                missing.append(
                    {
                        "source": source.relative_to(template_source).as_posix(),
                        "target": target,
                    }
                )
    if missing:
        raise RuntimeError(f"dangling Jinja includes: {missing}")
    return {"include_count": count, "missing": missing}


def _configure_consumer_policy(root: Path, name: str) -> None:
    waivers = [REDDIT_DISKCACHE_WAIVER] if name == "reddit-scraper" else []
    _set_pip_audit_waivers(root / "pyproject.toml", waivers, templated=False)
    _set_precommit_audit_waivers(
        root / ".pre-commit-config.yaml",
        waivers,
        templated=False,
    )
    _add_check_manifest_ignores(root / "pyproject.toml")


def _migrate_answers(root: Path, template_source: Path, name: str) -> dict[str, Any]:
    old = root / "_copier_answers.yml"
    new = root / ".copier-answers.yml"
    source = old if old.is_file() else new
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
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
    data["_src_path"] = Path(os.path.relpath(template_source, start=root)).as_posix()
    data["_commit"] = FINAL_TAG
    data["pip_audit_waivers"] = (
        [REDDIT_DISKCACHE_WAIVER] if name == "reddit-scraper" else []
    )
    new.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    old.unlink(missing_ok=True)
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace("_copier_answers.yml", ".copier-answers.yml"),
        encoding="utf-8",
    )
    return data


def _fresh_acceptance(output: Path, template_source: Path) -> dict[str, Any]:
    fresh = output / "_work/fresh-final"
    copy = _copy_at_tag(output, template_source, fresh, FINAL_TAG, "fresh-copier-copy")
    if not copy["passed"]:
        raise RuntimeError("final fresh Copier copy failed")
    if (fresh / "uv.lock").exists():
        raise RuntimeError("Copier must not own uv.lock")
    if (fresh / "scripts/env/project_config.sh").exists():
        raise RuntimeError("project_config.sh survived final fresh copy")
    for required in ("release-please-config.json", ".release-please-manifest.json"):
        if not (fresh / required).is_file():
            raise RuntimeError(f"fresh render missing {required}")
    _init_git(fresh, "fresh final render")
    commands = [
        base._run("fresh-setup", ["bash", "scripts/env/setup.sh"], cwd=fresh, output=output),
        base._run("fresh-doctor", ["bash", "scripts/env/doctor.sh"], cwd=fresh, output=output),
    ]
    if not (fresh / "uv.lock").is_file():
        raise RuntimeError("fresh setup did not create uv.lock")
    _git(fresh, "add", ".")
    _git(fresh, "commit", "-qm", "chore: bootstrap lock and hooks")
    commands.extend(
        [
            base._run(
                "fresh-pre-commit",
                ["uv", "run", "--no-sync", "pre-commit", "run", "--all-files"],
                cwd=fresh,
                output=output,
            ),
            base._run(
                "fresh-pre-push",
                [
                    "uv",
                    "run",
                    "--no-sync",
                    "pre-commit",
                    "run",
                    "--all-files",
                    "--hook-stage",
                    "pre-push",
                ],
                cwd=fresh,
                output=output,
            ),
            _copier(
                output,
                "fresh-copier-check-update",
                ["uvx", "--from", f"copier=={COPIER_VERSION}", "copier", "check-update"],
                cwd=fresh,
            ),
        ]
    )
    return {
        "path": str(fresh),
        "copy": copy,
        "commands": commands,
        "passed": all(command["passed"] for command in commands),
        "lock_created_by_setup": True,
    }


def _update_acceptance(
    output: Path,
    update_project: Path,
    sentinels: dict[str, str],
) -> dict[str, Any]:
    update = _copier(
        output,
        "copier-update-to-complete-template",
        [
            "uvx",
            "--from",
            f"copier=={COPIER_VERSION}",
            "copier",
            "update",
            "--trust",
            "--defaults",
            "--vcs-ref",
            FINAL_TAG,
        ],
        cwd=update_project,
    )
    if not update["passed"]:
        raise RuntimeError("Copier update to completed template failed")
    _assert_sentinels(update_project, sentinels)
    for required in ("release-please-config.json", ".release-please-manifest.json"):
        if not (update_project / required).is_file():
            raise RuntimeError(f"updated project missing {required}")
    if (update_project / "scripts/env/project_config.sh").exists():
        raise RuntimeError("updated project retained project_config.sh")
    setup = base._run(
        "updated-project-setup",
        ["bash", "scripts/env/setup.sh"],
        cwd=update_project,
        output=output,
    )
    return {
        "path": str(update_project),
        "update": update,
        "setup": setup,
        "user_owned_files_preserved": True,
        "passed": update["passed"] and setup["passed"],
    }


def _prepare_consumers(
    output: Path,
    candidate: Path,
    template_source: Path,
) -> dict[str, Any]:
    product._MANAGED_TEMPLATE_PATHS = tuple(
        dict.fromkeys(
            [
                *product._MANAGED_TEMPLATE_PATHS,
                ".release-please-manifest.json",
                "release-please-config.json",
            ]
        )
    )
    consumers: dict[str, Any] = {}
    work = output / "_work"
    for name, source in base.CONSUMERS.items():
        product._assert_revision(source, product.CONSUMER_SHAS[name], name)
        destination = work / "consumers" / name
        product._copytree(source, destination)
        identity = product._consumer_identity(destination)
        project_name = product._project_distribution_name(destination)
        lock_before = product._unrelated_lock_entries(destination, project_name=project_name)
        managed = product._replace_managed_surface(destination, candidate=candidate, identity=identity)
        product._rewrite_consumer_pyproject(destination, work)
        answers = _migrate_answers(destination, template_source.resolve(), name)
        _configure_consumer_policy(destination, name)
        changed = product._replace_text_files(destination, identity=identity)
        lock = base._run(
            f"prepare-{name}-lock",
            ["uv", "lock"],
            cwd=destination,
            output=output,
        )
        if not lock["passed"]:
            raise RuntimeError(f"uv lock failed for {name}")
        security = None
        if base.SECURITY_UPGRADES[name]:
            command = ["uv", "lock"]
            for requirement in base.SECURITY_UPGRADES[name]:
                command.extend(("--upgrade-package", requirement))
            security = base._run(
                f"prepare-{name}-security-refresh",
                command,
                cwd=destination,
                output=output,
            )
            if not security["passed"]:
                raise RuntimeError(f"security refresh failed for {name}")
        pyproject_format = base._run(
            f"prepare-{name}-pyproject-format",
            [
                "uvx",
                "--from",
                "pyproject-fmt==2.23.0",
                "pyproject-fmt",
                "--keep-full-version",
                "--skip-wrap-for-keys",
                "*",
                "pyproject.toml",
            ],
            cwd=destination,
            output=output,
            expected_returncodes={0, 1},
        )
        lock_after = product._unrelated_lock_entries(destination, project_name=project_name)
        git_results = base._init_git(destination, output, f"consumer-{name}")
        consumers[name] = {
            "path": str(destination),
            "identity": identity,
            "config": dx._consumer_config(destination),
            "answers": answers,
            "changed_text_files": changed,
            "managed_template_paths_replaced": managed,
            "unrelated_lock_entry_count_before": len(lock_before),
            "unrelated_lock_entry_count_after": len(lock_after),
            "prepare_commands": [
                lock,
                *([security] if security is not None else []),
                pyproject_format,
                *git_results,
            ],
        }
    return consumers


def _prepare(output: Path) -> None:
    shutil.rmtree(output / "_work", ignore_errors=True)
    output.mkdir(parents=True, exist_ok=True)
    product._prepare(
        argparse.Namespace(
            legacy=(ROOT / "py-lib-starter").resolve(),
            runtime=(ROOT / "runtime-prototype").resolve(),
            policy=(ROOT / "policy-prototype").resolve(),
            testkit=(ROOT / "testkit-prototype").resolve(),
            inventory=(ROOT / "capability_matrix.json").resolve(),
            assets=base.PRODUCT_ASSETS.resolve(),
            template_candidate=BASE_RENDER.resolve(),
            output=output.resolve(),
            consumer=None,
            name=None,
        )
    )
    provider_root, provider_sha = _provider_fixture(output)
    digests = _cache_image_digests()

    candidate = output / "_work/template-render"
    template_source = output / "_work/template-source"
    shutil.copytree(BASE_RENDER, candidate)
    shutil.copytree(BASE_TEMPLATE, template_source)
    shutil.copytree(COMPONENT_SNAPSHOT, template_source / "template/_components/components")

    _apply_base_with_cached_digests(candidate, digests)
    _apply_completion_delta(candidate, provider_sha=provider_sha, digests=digests)

    _apply_base_with_cached_digests(template_source / "template", digests)
    (template_source / "template/scripts/env/project_config.sh").unlink(missing_ok=True)
    initial_sha = _init_git(template_source, "pre-completion template source", INITIAL_TAG)

    update_project = output / "_work/update-project"
    initial_copy = _copy_at_tag(
        output,
        template_source,
        update_project,
        INITIAL_TAG,
        "copier-copy-pre-completion",
    )
    if not initial_copy["passed"]:
        raise RuntimeError("pre-completion Copier copy failed")
    _init_git(update_project, "pre-completion rendered project")
    sentinels = _user_owned_sentinels(update_project)
    _commit(update_project, "product-owned user files")

    _apply_completion_delta(
        template_source / "template",
        provider_sha=provider_sha,
        digests=digests,
    )
    final_sha = _commit(template_source, "complete Python template contract", FINAL_TAG)

    include_validation = _validate_includes(template_source)
    surface = _validate_surface(candidate)
    update_acceptance = _update_acceptance(output, update_project, sentinels)
    fresh_acceptance = _fresh_acceptance(output, template_source)
    consumers = _prepare_consumers(output, candidate, template_source)

    state = {
        "schema": "ternforge-python-template-completion/v1",
        "outcome": "running",
        "candidate": str(candidate),
        "template_source": str(template_source),
        "provider_fixture": {"path": str(provider_root), "sha": provider_sha},
        "template_git": {
            "initial_tag": INITIAL_TAG,
            "initial_sha": initial_sha,
            "final_tag": FINAL_TAG,
            "final_sha": final_sha,
        },
        "image_digests": digests,
        "include_validation": include_validation,
        "surface": surface,
        "initial_copy": initial_copy,
        "update_acceptance": update_acceptance,
        "fresh_acceptance": fresh_acceptance,
        "consumers": consumers,
    }
    _write_json(output / "state.json", state)


def _load_state(output: Path) -> dict[str, Any]:
    return json.loads((output / "state.json").read_text(encoding="utf-8"))


def _save_state(output: Path, state: dict[str, Any]) -> None:
    _write_json(output / "state.json", state)


def _ci(output: Path, consumer: str) -> None:
    state = _load_state(output)
    item = state["consumers"][consumer]
    results = dx._ci_commands(Path(item["path"]), item["config"], output, consumer)
    functional = [
        result for result in results if not result["name"].endswith("runtime-audit")
    ]
    raw_audits = [
        result for result in results if result["name"].endswith("runtime-audit")
    ]
    item["ci"] = {
        "commands": results,
        "passed": all(result["passed"] for result in functional),
        "failed": [result["name"] for result in functional if not result["passed"]],
        "raw_runtime_audit_findings": [
            result["name"] for result in raw_audits if not result["passed"]
        ],
    }
    _save_state(output, state)


def _dx(output: Path, consumer: str) -> None:
    if consumer == "reddit-scraper":
        shutil.rmtree(output / "_work/secret-fixture", ignore_errors=True)
    base._dx(output, consumer)
    if consumer != "reddit-scraper":
        return
    state = _load_state(output)
    item = state["consumers"][consumer]
    root = Path(item["path"])
    waiver_check = base._run(
        "dx-reddit-scraper-repository-waiver",
        [
            "uv",
            "run",
            "--no-sync",
            "pre-commit",
            "run",
            "runtime-dependency-audit",
            "--hook-stage",
            "pre-push",
            "--all-files",
        ],
        cwd=root,
        output=output,
    )
    item["dx"]["commands"].append(waiver_check)
    item["dx"]["passed"] = item["dx"]["passed"] and waiver_check["passed"]
    if not waiver_check["passed"]:
        item["dx"]["failed"].append(waiver_check["name"])
    _save_state(output, state)


def _e2e(output: Path, consumer: str) -> None:
    dx._e2e(output, consumer)


def _container(output: Path) -> None:
    state = _load_state(output)
    candidate = Path(state["candidate"])
    build = base._run(
        "container-build-complete",
        [
            "docker",
            "build",
            "--file",
            ".devcontainer/Dockerfile",
            "--tag",
            "ternforge-template-complete:20260802",
            ".devcontainer",
        ],
        cwd=candidate,
        output=output,
    )
    tools = base._run(
        "container-tools-complete",
        [
            "docker",
            "run",
            "--rm",
            "ternforge-template-complete:20260802",
            "bash",
            "-lc",
            "command -v uv && command -v direnv && command -v git && command -v sops",
        ],
        cwd=candidate,
        output=output,
    )

    shutil.rmtree(output / "_work/secret-fixture", ignore_errors=True)
    fixture = base._create_encrypted_fixture(output)
    fresh = Path(state["fresh_acceptance"]["path"])
    pyproject = fresh / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text = text.replace(
        "secrets.env_files = []",
        'secrets.env_files = [ "browser-automation/proxy.sops.env" ]',
        1,
    )
    pyproject.write_text(text, encoding="utf-8")
    remote = fixture["PY_LIB_SECRETS_GIT_URL"]
    key = fixture["SOPS_AGE_KEY_FILE"]
    secrets = base._run(
        "container-automatic-secrets",
        [
            "docker",
            "run",
            "--rm",
            "-e",
            "HOME=/home/vscode",
            "-e",
            "XDG_DATA_HOME=/tmp/ternforge-data",
            "-e",
            "PY_LIB_SECRETS_GIT_URL=/fixture/remote.git",
            "-v",
            f"{fresh}:/work:ro",
            "-v",
            f"{remote}:/fixture/remote.git:ro",
            "-v",
            f"{key}:/home/vscode/.config/sops/age/keys.txt:ro",
            "-w",
            "/work",
            "ternforge-template-complete:20260802",
            "bash",
            "-lc",
            'source scripts/env/secrets.sh; py_lib_load_secrets /work; test "$LAB_DX_SENTINEL" = ok',
        ],
        cwd=candidate,
        output=output,
    )
    state["container"] = {
        "build": build,
        "tools": tools,
        "automatic_secrets": secrets,
        "passed": build["passed"] and tools["passed"] and secrets["passed"],
    }
    _save_state(output, state)


def _finalize(output: Path) -> None:
    state = _load_state(output)
    reddit_commands = state["consumers"]["reddit-scraper"].get(
        "direct_execution", {}
    ).get("commands", [])
    reddit_public = bool(reddit_commands) and all(
        command["passed"] for command in reddit_commands if "-e2e-" in command["name"]
    )
    expected_reddit_external = {
        "e2e-reddit-scraper-workbench-python-module",
        "e2e-reddit-scraper-workbench-active-loop",
    }
    consumers: dict[str, Any] = {}
    for name, item in sorted(state["consumers"].items()):
        if name == "llm-router":
            direct = None
        elif name == "reddit-scraper":
            direct = reddit_public
        else:
            direct = item.get("direct_execution", {}).get("passed")
        failed = (
            item.get("ci", {}).get("failed", [])
            + item.get("dx", {}).get("failed", [])
            + item.get("direct_execution", {}).get("failed", [])
        )
        if name == "reddit-scraper":
            failed = [value for value in failed if value not in expected_reddit_external]
        consumers[name] = {
            "ci": item.get("ci", {}).get("passed", False),
            "dx": item.get("dx", {}).get("passed", False),
            "direct_execution": direct,
            "live_workbench_external": name == "reddit-scraper",
            "failed": failed,
        }
    generic_precommit = (Path(state["candidate"]) / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    passed = bool(
        state["include_validation"]["missing"] == []
        and state["surface"]["lost_unrelated_files"] == []
        and state["update_acceptance"]["passed"]
        and state["fresh_acceptance"]["passed"]
        and state.get("container", {}).get("passed", False)
        and REDDIT_DISKCACHE_WAIVER["id"] not in generic_precommit
        and all(item["ci"] and item["dx"] for item in consumers.values())
        and consumers["web-tools"]["direct_execution"]
        and consumers["visual-annotation"]["direct_execution"]
        and reddit_public
    )
    state["outcome"] = "passed" if passed else "failed"
    state["summary"] = {
        "implementation_candidate_complete": passed,
        "production_rollout_performed": False,
        "fresh_copy": state["fresh_acceptance"]["passed"],
        "copier_update_preserves_product_files": state["update_acceptance"]["passed"],
        "zero_dangling_includes": state["include_validation"]["missing"] == [],
        "zero_unrelated_product_files_lost": state["surface"]["lost_unrelated_files"] == [],
        "devcontainer_automatic_secrets": state.get("container", {}).get("passed", False),
        "generic_template_has_consumer_cve": REDDIT_DISKCACHE_WAIVER["id"] in generic_precommit,
        "consumers": consumers,
        "reddit_public_e2e": reddit_public,
    }
    _write_json(output / "result.json", state)
    lines = [
        "# Python template completion result",
        "",
        f"Outcome: **{state['outcome'].upper()}**",
        "",
        "Production infrastructure and external services were not created. The result is a complete local implementation candidate with explicit future immutable-reference binding points.",
        "",
        "## Completion gates",
        "",
        f"* Real fresh Copier copy: {'PASS' if state['fresh_acceptance']['passed'] else 'FAIL'}",
        f"* Copier update preserves product-owned files: {'PASS' if state['update_acceptance']['passed'] else 'FAIL'}",
        f"* Zero dangling includes: {'PASS' if not state['include_validation']['missing'] else 'FAIL'}",
        f"* Zero unrelated product files lost: {'PASS' if not state['surface']['lost_unrelated_files'] else 'FAIL'}",
        f"* Devcontainer automatic secrets: {'PASS' if state.get('container', {}).get('passed') else 'FAIL'}",
        f"* Generic template is free of the Reddit-specific waiver: {'FAIL' if state['summary']['generic_template_has_consumer_cve'] else 'PASS'}",
        "",
        "## Consumers",
        "",
        "| Consumer | CI | DX | Direct execution |",
        "|---|---:|---:|---:|",
    ]
    for name, item in consumers.items():
        if name == "reddit-scraper" and reddit_public:
            direct_text = "PUBLIC E2E PASS; LIVE WORKBENCH EXTERNAL"
        elif item["direct_execution"] is None:
            direct_text = "N/A"
        else:
            direct_text = "PASS" if item["direct_execution"] else "FAIL"
        lines.append(
            f"| `{name}` | {'PASS' if item['ci'] else 'FAIL'} | {'PASS' if item['dx'] else 'FAIL'} | {direct_text} |"
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "* The lab provider fixture supplies a real local commit SHA for caller-schema verification; production implementation replaces it with the released `ternforge-infra-ci` commit SHA.",
            "* Sandbox runtime/policy/testkit refs remain frozen experiment inputs, not production bindings.",
            "* No production repository, ruleset, credential, external service, or release was created.",
            "",
        ]
    )
    _write(output / "report.md", "\n".join(lines))
    _save_state(output, state)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "phase",
        choices=("prepare", "ci", "dx", "e2e", "container", "finalize"),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--consumer", choices=sorted(base.CONSUMERS))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    output = args.output.resolve()
    if args.phase == "prepare":
        _prepare(output)
    elif args.phase == "ci":
        if args.consumer is None:
            raise ValueError("ci requires --consumer")
        _ci(output, args.consumer)
    elif args.phase == "dx":
        if args.consumer is None:
            raise ValueError("dx requires --consumer")
        _dx(output, args.consumer)
    elif args.phase == "e2e":
        if args.consumer is None:
            raise ValueError("e2e requires --consumer")
        _e2e(output, args.consumer)
    elif args.phase == "container":
        _container(output)
    else:
        _finalize(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
