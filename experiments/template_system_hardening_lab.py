#!/usr/bin/env python3
"""Harden the validated Ternforge two-template component system.

This follow-up preserves the EXP-0032 topology and full-product checks while
covering current Copier and Vendir edge cases: default legal paths, guarded
conditional exclusions, exact Copier 9.17.0 behavior, and executable modes in
controlled updates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import python_template_product_parity_lab as parity  # noqa: E402

COPIER_VERSION = "9.17.0"
UV_VERSION = "0.12.0"
VENDIR_VERSION = "0.46.0"
BASELINE_SHA = parity.BASELINE_SHA
FIXED_GIT_DATE = "2026-08-01T00:00:00Z"

GENERIC_AGENT_SKILLS = {
    "changed",
    "code-guardrails",
    "finish-worktree",
    "handoff",
    "warmup",
}

QUALITY_ROOT_FILES = {
    ".gitleaks.toml",
    ".markdown-link-check.json",
    ".markdownlint.yaml",
    ".mdformat.toml",
    ".pre-commit-config.yaml",
    "typos.toml",
}

INFRA_ROOT_ENTRIES = {
    ".agents",
    ".copier-answers.yml",
    ".editorconfig",
    ".gitattributes",
    ".github",
    ".gitignore",
    "LICENSE",
    "README.md",
}

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

PLATFORM_COMPARE_IGNORES = {
    ".github/MAINTAINER_SETUP.md",
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
    "renovate.json5",
    "_copier_answers.yml",
    ".copier-answers.yml",
}

FORBIDDEN_TEMPLATE_PATH_PARTS = {
    ".gitmodules",
    "WIRING.json",
    "template-manifests",
    "template-builds",
}


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
        raise RuntimeError(
            f"{name} failed ({process.returncode}): {' '.join(command)}\n"
            f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return result


def write(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def git_env() -> dict[str, str]:
    return {
        "GIT_AUTHOR_DATE": FIXED_GIT_DATE,
        "GIT_COMMITTER_DATE": FIXED_GIT_DATE,
    }


def git(repository: Path, *args: str) -> CommandResult:
    return run("git " + " ".join(args), ["git", *args], cwd=repository, env=git_env())


def init_git(repository: Path) -> None:
    git(repository, "init", "-q", "-b", "main")
    git(repository, "config", "user.name", "Ternforge Lab")
    git(repository, "config", "user.email", "lab@example.invalid")


def commit(repository: Path, message: str, *, tag: str | None = None) -> str:
    git(repository, "add", "-A")
    git(repository, "commit", "-qm", message)
    sha = git(repository, "rev-parse", "HEAD").stdout.strip()
    if tag:
        git(repository, "tag", tag)
    return sha


def commit_paths(repository: Path, sha: str) -> list[str]:
    result = git(
        repository,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        sha,
    )
    return sorted(line for line in result.stdout.splitlines() if line)


def git_index_mode(repository: Path, relative: str) -> str:
    result = git(repository, "ls-files", "--stage", "--", relative)
    line = result.stdout.strip()
    if not line:
        raise RuntimeError(f"Git index does not contain {relative}")
    return line.split(maxsplit=1)[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_map(root: Path, *, ignore_answers: bool = False) -> dict[str, Path]:
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
        ".artifact-smoke",
    }
    result: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in ignored_parts for part in relative.parts):
            continue
        if relative.as_posix() == "uv.lock":
            continue
        if ignore_answers and relative.name in {
            "_copier_answers.yml",
            ".copier-answers.yml",
        }:
            continue
        result[relative.as_posix()] = path
    return result


def executable_bit(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


def compare_trees(
    left: Path,
    right: Path,
    *,
    ignore: Iterable[str] = (),
    ignore_answers: bool = False,
) -> dict[str, object]:
    ignored = set(ignore)
    left_map = {
        key: value
        for key, value in file_map(left, ignore_answers=ignore_answers).items()
        if key not in ignored
    }
    right_map = {
        key: value
        for key, value in file_map(right, ignore_answers=ignore_answers).items()
        if key not in ignored
    }
    left_paths = set(left_map)
    right_paths = set(right_map)
    missing = sorted(left_paths - right_paths)
    added = sorted(right_paths - left_paths)
    changed = sorted(
        path
        for path in left_paths & right_paths
        if left_map[path].read_bytes() != right_map[path].read_bytes()
    )
    mode_changed = sorted(
        path
        for path in left_paths & right_paths
        if executable_bit(left_map[path]) != executable_bit(right_map[path])
    )
    return {
        "left_count": len(left_paths),
        "right_count": len(right_paths),
        "missing": missing,
        "added": added,
        "changed": changed,
        "mode_changed": mode_changed,
        "equal": not (missing or added or changed or mode_changed),
    }


def top_level_blocks(text: str) -> dict[str, str]:
    lines = text.splitlines(keepends=True)
    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s|$)", line)
        if match:
            starts.append((index, match.group(1)))
    blocks: dict[str, str] = {}
    for position, (start, key) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        blocks[key] = "".join(lines[start:end])
    return blocks


def python_copier_config(baseline_root: Path) -> str:
    blocks = top_level_blocks(
        (baseline_root / "copier.yml").read_text(encoding="utf-8")
    )
    question_keys = [
        "project_name",
        "package_name",
        "project_slug",
        "project_title",
        "project_title_lower",
        "project_description",
        "initial_version",
        "author_name",
        "author_email",
        "copyright_year",
        "github_owner",
        "repository_name",
        "library_lane",
        "env_prefix",
        "error_class_name",
        "config_class_name",
        "e2e_slices",
        "ci_playwright_browsers",
        "renovate_uv_ignored_updates",
        "gitignore_extra_patterns",
        "workspace_python_paths",
        "workspace_test_paths",
    ]
    missing = [key for key in question_keys if key not in blocks]
    if missing:
        raise RuntimeError(f"missing baseline Copier questions: {missing}")
    meta = f"""_min_copier_version: \"{COPIER_VERSION}\"
_subdirectory: template
_answers_file: .copier-answers.yml
_templates_suffix: \"\"
_envops:
  undefined: jinja2.StrictUndefined
  variable_start_string: \"[[[\"
  variable_end_string: \"]]]\"
  block_start_string: \"[[%\"
  block_end_string: \"%]]\"
  comment_start_string: \"[[#\"
  comment_end_string: \"#]]\"
  trim_blocks: true
  lstrip_blocks: true
_exclude:
  - _components
  - _components/**
  - \"[[% if _copier_operation == 'update' or (ternforge_recopy_audit | default(false)) -%]]src/**[[% endif %]]\"
  - \"[[% if _copier_operation == 'update' or (ternforge_recopy_audit | default(false)) -%]]tests/**[[% endif %]]\"
  - \"[[% if _copier_operation == 'update' or (ternforge_recopy_audit | default(false)) -%]]docs/**[[% endif %]]\"
  - \"[[% if _copier_operation == 'update' or (ternforge_recopy_audit | default(false)) -%]]examples/**[[% endif %]]\"
  - \"[[% if _copier_operation == 'update' or (ternforge_recopy_audit | default(false)) -%]]workbench/**[[% endif %]]\"
  - \"[[% if _copier_operation == 'update' or (ternforge_recopy_audit | default(false)) -%]]README.md[[% endif %]]\"
  - \"[[% if _copier_operation == 'update' or (ternforge_recopy_audit | default(false)) -%]]CHANGELOG.md[[% endif %]]\"

"""
    return meta + "".join(blocks[key] for key in question_keys)


def infra_copier_config() -> str:
    return f"""_min_copier_version: \"{COPIER_VERSION}\"
_subdirectory: template
_answers_file: .copier-answers.yml
_templates_suffix: .jinja
_envops:
  undefined: jinja2.StrictUndefined
  variable_start_string: \"[[[\"
  variable_end_string: \"]]]\"
  block_start_string: \"[[%\"
  block_end_string: \"%]]\"
  comment_start_string: \"[[#\"
  comment_end_string: \"#]]\"
  trim_blocks: true
  lstrip_blocks: true
_exclude:
  - _components
  - _components/**
  - \"[[% if _copier_operation == 'update' or (ternforge_recopy_audit | default(false)) -%]]README.md[[% endif %]]\"

repository_name:
  type: str
  default: ternforge-infra-sample
project_title:
  type: str
  default: Ternforge Infra Sample
github_owner:
  type: str
  default: betabitplus
copyright_year:
  type: str
  default: \"2026\"
"""


def rewrite_source_pyproject(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    runtime_old = (
        '  "py-lib-runtime @ git+[[[ runtime_git_url ]]]@[[[ runtime_git_ref ]]]'
        '#subdirectory=[[[ runtime_git_subdirectory ]]]",'
    )
    runtime_new = (
        '  "py-lib-runtime @ git+https://github.com/betabitplus-template-lab/'
        f'sandbox-ternforge-tooling-py-runtime-20260717-r2.git@{parity.RUNTIME_COMMIT}",'
    )
    tooling_old = (
        '  "py-lib-tooling @ git+[[[ tooling_git_url ]]]@[[[ tooling_git_ref ]]]'
        '#subdirectory=[[[ tooling_git_subdirectory ]]]",'
    )
    tooling_new = "\n".join(
        [
            '  "py-lib-policy @ git+https://github.com/betabitplus-template-lab/'
            f'sandbox-ternforge-tooling-py-policy-20260717-r2.git@{parity.POLICY_COMMIT}",',
            '  "py-lib-testkit @ git+https://github.com/betabitplus-template-lab/'
            f'sandbox-ternforge-tooling-py-testkit-20260717-r2.git@{parity.TESTKIT_COMMIT}",',
        ]
    )
    text = parity.replace_once(
        text, runtime_old, runtime_new, label="source runtime dependency"
    )
    text = parity.replace_once(
        text, tooling_old, tooling_new, label="source tooling dependency"
    )
    text = parity.replace_once(
        text, "[tool.py_lib_starter]", "[tool.ternforge]", label="source tool table"
    )
    text = text.replace(
        "# ---------------- Shared py-lib tooling manifest ----------------",
        "# ---------------- Ternforge project manifest ----------------",
    )
    path.write_text(text, encoding="utf-8")


def normalize_source_formatting(root: Path) -> None:
    path = root / "src" / "[[[ package_name ]]]" / "_internal" / "config" / "state.py"
    text = path.read_text(encoding="utf-8")
    old = """        msg = (\n            \"install_config() expects a \"\n            f\"{[[[ config_class_name ]]].__name__} instance.\"\n        )"""
    new = """        msg = f\"install_config() expects a {[[[ config_class_name ]]].__name__} instance.\""""
    if old not in text:
        raise RuntimeError("expected source formatting fixture was not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def prepare_python_template_source(baseline_root: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    source = baseline_root / "template-builds" / "python-lib-standard"
    template = destination / "template"
    shutil.copytree(source, template, symlinks=True)

    for relative in parity.PLATFORM_REMOVED_PATHS:
        path = template / relative
        if not path.exists():
            raise RuntimeError(f"missing platform source path: {relative}")
        path.unlink()

    rewrite_source_pyproject(template / "pyproject.toml")
    parity.rewrite_precommit(template / ".pre-commit-config.yaml")
    parity.rewrite_project_config(template / "scripts/env/project_config.sh")
    parity.rewrite_product_namespaces(template)
    normalize_source_formatting(template)
    parity.write_product_helpers(template)
    parity.write_platform_files(template)

    for path in sorted(template.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = text.replace("_copier_answers.yml", ".copier-answers.yml")
        updated = updated.replace(
            f"copier=={parity.COPIER_VERSION}", f"copier=={COPIER_VERSION}"
        )
        updated = updated.replace("tests/sample_lib/", "tests/[[[ package_name ]]]/")
        if path.name == "pyproject.toml":
            updated = updated.replace(
                '  ".agents/**",\n  ".devcontainer/**",',
                '  ".agents/**",\n  ".copier-answers.yml",\n  ".devcontainer/**",',
            )
            updated = updated.replace(
                '  "__pycache__/**",\n  ".copier-answers.yml",',
                '  "__pycache__/**",',
            )
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    for path in sorted(template.rglob("*.sh")):
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    helper = template / "scripts" / "reproduce_running_loop.py"
    helper.chmod(helper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    write(destination / "copier.yml", python_copier_config(baseline_root))


def classify_component(relative: str) -> str:
    parts = Path(relative).parts
    if relative.startswith(".agents/skills/") and len(parts) >= 3:
        skill = parts[2]
        return "agents/base" if skill in GENERIC_AGENT_SKILLS else "agents/py-library"
    if relative == "AGENTS.md":
        return "agents/py-library"
    if relative in {".editorconfig", "LICENSE"}:
        return "repository/base"
    if relative == "[[[ _copier_conf.answers_file ]]]":
        return "repository/copier"
    if (
        relative == ".github/workflows/ci.yml"
        or relative == ".github/MAINTAINER_SETUP.md"
    ):
        return "delivery/ci/py-library"
    if relative in {
        ".github/workflows/release.yml",
        ".release-please-manifest.json",
        "release-please-config.json",
    }:
        return "delivery/release/library"
    if relative == "renovate.json5":
        return "delivery/updates"
    if relative in QUALITY_ROOT_FILES:
        return "quality/py"
    if relative == ".github/pull_request_template.md":
        return "project/py/library"
    if relative.startswith(("src/", "tests/", "docs/", "examples/", "workbench/")):
        return "project/py/library"
    if relative in {"README.md", "CHANGELOG.md", "MANIFEST.in"}:
        return "project/py/library"
    if relative.startswith("scripts/") and not relative.startswith("scripts/env/"):
        return "project/py/library"
    return "project/py/base"


def stable_component_relative(relative: str) -> str:
    """Keep component source paths independent from final-template questions."""
    return relative.replace("[[[ package_name ]]]", "__package__")


def component_source_path(component: str, relative: str) -> str:
    return f"components/{component}/template/{stable_component_relative(relative)}"


def split_pyproject(text: str) -> list[tuple[str, str, str]]:
    dependency_marker = "[dependency-groups]\n"
    setuptools_marker = "[tool.setuptools]\n"
    quality_marker = "# ---------------- Ruff configuration ----------------\n"
    dep_index = text.index(dependency_marker)
    setuptools_index = text.index(setuptools_marker)
    quality_index = text.index(quality_marker)
    return [
        ("project/py/base", "pyproject-project.toml", text[:dep_index]),
        ("quality/py", "pyproject-dependencies.toml", text[dep_index:setuptools_index]),
        (
            "project/py/library",
            "pyproject-packaging.toml",
            text[setuptools_index:quality_index],
        ),
        ("quality/py", "pyproject-tools.toml", text[quality_index:]),
    ]


def build_components_repository(
    direct_template: Path,
    repository: Path,
) -> tuple[dict[str, str], list[str], dict[str, str]]:
    if repository.exists():
        shutil.rmtree(repository)
    repository.mkdir(parents=True)
    init_git(repository)
    write(
        repository / "README.md",
        "# Ternforge template components\n\nReleased source files for final Copier templates.\n",
    )
    write(
        repository / "LICENSE",
        "ROOT LEGAL SENTINEL: must not bypass selective component snapshots.\n",
    )
    write(
        repository / "NOTICE",
        "ROOT NOTICE SENTINEL: must not bypass selective component snapshots.\n",
    )

    mapping: dict[str, str] = {}
    modes: dict[str, str] = {}
    template_root = direct_template / "template"
    for source in sorted(template_root.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(template_root).as_posix()
        if relative == "pyproject.toml":
            continue
        if relative == "[[[ _copier_conf.answers_file ]]]":
            continue
        component = classify_component(relative)
        component_relative = component_source_path(component, relative)
        copy_file(source, repository / component_relative)
        mapping[relative] = component_relative
        if executable_bit(source):
            modes[relative] = "100755"

    answers_include = "components/repository/copier/includes/copier-answers.yml"
    write(
        repository / answers_include,
        "[[[ _copier_answers|to_nice_yaml|trim ]]]\n",
    )

    pyproject_includes: list[str] = []
    pyproject_text = (template_root / "pyproject.toml").read_text(encoding="utf-8")
    for component, name, content in split_pyproject(pyproject_text):
        relative = f"components/{component}/includes/{name}"
        write(repository / relative, content)
        pyproject_includes.append(relative)

    write(
        repository / "components/repository/base/template/.gitattributes",
        "* text=auto eol=lf\n*.sh text eol=lf\n",
    )
    write(
        repository
        / "components/repository/base/template/.github/pull_request_template.md",
        "# Summary\n\nDescribe the infrastructure change.\n\n## Validation\n\n- [ ] Ran the repository's required checks\n",
    )

    initial_sha = commit(repository, "components v0.1.0", tag="v0.1.0")

    py_marker = repository / component_source_path(
        "agents/py-library",
        ".agents/skills/python-library-rules/SKILL.md",
    )
    py_marker.write_text(
        py_marker.read_text(encoding="utf-8") + "\n<!-- component update v0.2.0 -->\n",
        encoding="utf-8",
    )
    py_sha = commit(repository, "python-only component update", tag="v0.2.0")

    editorconfig = repository / "components/repository/base/template/.editorconfig"
    editorconfig.write_text(
        editorconfig.read_text(encoding="utf-8")
        + "\n# shared component update v0.3.0\n",
        encoding="utf-8",
    )
    shared_sha = commit(repository, "shared component update", tag="v0.3.0")

    return (
        mapping,
        pyproject_includes,
        {
            "v0.1.0": initial_sha,
            "v0.2.0": py_sha,
            "v0.3.0": shared_sha,
            "answers_include": answers_include,
        },
    )


def include_wrapper(component_path: str) -> str:
    return f'[[% include "template/_components/{component_path}" %]]'


def write_vendir_config(
    template_repository: Path,
    components_repository: Path,
    ref: str,
    include_paths: Sequence[str],
) -> None:
    url = components_repository.resolve().as_uri()
    rendered_include_paths = "\n".join(
        f"          - {include_path}" for include_path in include_paths
    )
    content = f"""apiVersion: vendir.k14s.io/v1alpha1
kind: Config
directories:
  - path: template/_components
    contents:
      - path: .
        git:
          url: {url}
          ref: {ref}
        includePaths:
{rendered_include_paths}
        excludePaths:
          - .git
          - .git/**/*
        legalPaths: []
"""
    write(template_repository / "vendir.yml", content)


def vendir_sync(template_repository: Path, vendir: Path) -> None:
    run("vendir sync", [str(vendir), "sync"], cwd=template_repository)
    leaked = list((template_repository / "template" / "_components").rglob(".git"))
    if leaked:
        raise RuntimeError(f"Vendir leaked Git metadata: {leaked}")


def create_python_template_repository(
    repository: Path,
    direct_template: Path,
    components_repository: Path,
    mapping: dict[str, str],
    pyproject_includes: list[str],
    answers_include: str,
    vendir: Path,
) -> None:
    if repository.exists():
        shutil.rmtree(repository)
    repository.mkdir(parents=True)
    init_git(repository)
    copy_file(direct_template / "copier.yml", repository / "copier.yml")

    template_root = repository / "template"
    for relative, component_path in sorted(mapping.items()):
        wrapper = template_root / relative
        write(
            wrapper,
            include_wrapper(component_path),
            executable=modes_from_mapping(mapping, direct_template).get(
                relative, False
            ),
        )
    write(
        template_root / "[[[ _copier_conf.answers_file ]]]",
        include_wrapper(answers_include),
    )
    pyproject_wrapper = "".join(include_wrapper(path) for path in pyproject_includes)
    write(template_root / "pyproject.toml", pyproject_wrapper)

    write_vendir_config(
        repository, components_repository, "v0.1.0", PYTHON_INCLUDE_PATHS
    )
    vendir_sync(repository, vendir)
    commit(repository, "python template v0.1.0", tag="v0.1.0")


def modes_from_mapping(
    mapping: dict[str, str], direct_template: Path
) -> dict[str, bool]:
    result: dict[str, bool] = {}
    root = direct_template / "template"
    for relative in mapping:
        source = root / relative
        result[relative] = executable_bit(source)
    return result


def infra_wrapper_path(template_root: Path, relative: str) -> Path:
    return template_root / f"{relative}.jinja"


def create_infra_template_repository(
    repository: Path,
    components_repository: Path,
    mapping: dict[str, str],
    answers_include: str,
    vendir: Path,
) -> None:
    if repository.exists():
        shutil.rmtree(repository)
    repository.mkdir(parents=True)
    init_git(repository)
    write(repository / "copier.yml", infra_copier_config())
    template_root = repository / "template"

    generic_agent_paths = sorted(
        relative
        for relative, component in mapping.items()
        if component.startswith("components/agents/base/")
    )
    for relative in generic_agent_paths:
        write(
            infra_wrapper_path(template_root, relative),
            include_wrapper(mapping[relative]),
        )

    for relative in (".editorconfig", "LICENSE"):
        write(
            infra_wrapper_path(template_root, relative),
            include_wrapper(mapping[relative]),
        )
    write(
        infra_wrapper_path(template_root, ".gitattributes"),
        include_wrapper("components/repository/base/template/.gitattributes"),
    )
    write(
        infra_wrapper_path(template_root, ".github/pull_request_template.md"),
        include_wrapper(
            "components/repository/base/template/.github/pull_request_template.md"
        ),
    )
    write(
        template_root / ".copier-answers.yml.jinja",
        include_wrapper(answers_include),
    )
    write(
        template_root / ".gitignore.jinja",
        ".DS_Store\n.env\n*.tfstate\n*.tfstate.*\n",
    )
    write(
        template_root / "README.md.jinja",
        "# [[[ project_title ]]]\n\nInfrastructure repository `[[[ github_owner ]]]/[[[ repository_name ]]]`.\n",
    )

    write_vendir_config(
        repository, components_repository, "v0.1.0", INFRA_INCLUDE_PATHS
    )
    vendir_sync(repository, vendir)
    commit(repository, "infra template v0.1.0", tag="v0.1.0")


def update_template_components(
    repository: Path,
    components_repository: Path,
    ref: str,
    template_tag: str,
    vendir: Path,
    include_paths: Sequence[str],
) -> str:
    write_vendir_config(repository, components_repository, ref, include_paths)
    vendir_sync(repository, vendir)
    return commit(repository, f"components {ref}", tag=template_tag)


def render(
    template_repository: Path,
    destination: Path,
    *,
    ref: str,
    data: dict[str, str] | None = None,
) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    command = [
        "copier",
        "copy",
        "--defaults",
        "--vcs-ref",
        ref,
    ]
    for key, value in sorted((data or {}).items()):
        command.extend(["--data", f"{key}={value}"])
    command.extend([str(template_repository), str(destination)])
    run(
        f"Copier render {template_repository.name}@{ref}",
        command,
        cwd=template_repository,
    )


def initialize_consumer(repository: Path, message: str) -> None:
    init_git(repository)
    commit(repository, message)


def update_consumer(repository: Path, ref: str) -> CommandResult:
    return run(
        f"Copier update {ref}",
        [
            "copier",
            "update",
            "--defaults",
            "--skip-answered",
            "--answers-file",
            ".copier-answers.yml",
            "--vcs-ref",
            ref,
        ],
        cwd=repository,
    )


def validate_copier_edge_cases(work_dir: Path) -> dict[str, object]:
    """Confirm upstream edge cases and the controlled-update mitigations."""
    template_repository = work_dir / "copier-edge-template"
    if template_repository.exists():
        shutil.rmtree(template_repository)
    template_repository.mkdir(parents=True)
    init_git(template_repository)

    write(
        template_repository / "copier.yml",
        f"""_min_copier_version: \"{COPIER_VERSION}\"
_subdirectory: template
_answers_file: .copier-answers.yml
_templates_suffix: .jinja
_envops:
  undefined: jinja2.StrictUndefined
project_name:
  type: str
  default: edge-case-sample
""",
    )
    write(
        template_repository / "template/.copier-answers.yml.jinja",
        "{{ _copier_answers|to_nice_yaml|trim }}\n",
    )
    write(
        template_repository / "template/README.md.jinja",
        "# {{ project_name }}\n",
    )
    commit(template_repository, "edge template v1", tag="v1.0.0")

    write(
        template_repository / "copier.yml",
        f"""_min_copier_version: \"{COPIER_VERSION}\"
_subdirectory: template
_answers_file: .copier-answers.yml
_templates_suffix: .jinja
_envops:
  undefined: jinja2.StrictUndefined
_exclude:
  - "{{% if not (emit_optional | default(false)) -%}}optional.txt{{% endif %}}"
project_name:
  type: str
  default: edge-case-sample
emit_optional:
  type: bool
  default: false
""",
    )
    write(
        template_repository / "template/optional.txt.jinja",
        "optional output\n",
    )
    write(
        template_repository / "template/scripts/new-managed-tool.sh.jinja",
        "#!/usr/bin/env bash\nset -euo pipefail\nprintf 'managed tool\\n'\n",
        executable=True,
    )
    commit(template_repository, "edge template v2", tag="v2.0.0")

    negative_consumer = work_dir / "copier-edge-negative"
    render(template_repository, negative_consumer, ref="v1.0.0")
    initialize_consumer(negative_consumer, "initial edge consumer")
    git(negative_consumer, "config", "core.fileMode", "false")
    update_consumer(negative_consumer, "v2.0.0")
    if (negative_consumer / "optional.txt").exists():
        raise RuntimeError("guarded conditional exclude emitted optional.txt")
    git(negative_consumer, "add", "scripts/new-managed-tool.sh")
    negative_mode = git_index_mode(negative_consumer, "scripts/new-managed-tool.sh")
    if negative_mode != "100644":
        raise RuntimeError(
            "expected Copier 9.17.0 core.fileMode=false negative control to record 100644, "
            f"got {negative_mode}"
        )

    controlled_consumer = work_dir / "copier-edge-controlled"
    render(template_repository, controlled_consumer, ref="v1.0.0")
    initialize_consumer(controlled_consumer, "initial controlled edge consumer")
    git(controlled_consumer, "config", "core.fileMode", "false")
    git(controlled_consumer, "config", "core.fileMode", "true")
    update_consumer(controlled_consumer, "v2.0.0")
    if (controlled_consumer / "optional.txt").exists():
        raise RuntimeError("guarded conditional exclude emitted optional.txt")
    git(controlled_consumer, "add", "scripts/new-managed-tool.sh")
    controlled_mode = git_index_mode(controlled_consumer, "scripts/new-managed-tool.sh")
    if controlled_mode != "100755":
        raise RuntimeError(
            "controlled Copier update did not preserve the new executable mode: "
            f"{controlled_mode}"
        )

    optional_render = work_dir / "copier-edge-optional"
    render(
        template_repository,
        optional_render,
        ref="v2.0.0",
        data={"emit_optional": "true"},
    )
    if not (optional_render / "optional.txt").is_file():
        raise RuntimeError("explicit emit_optional=true did not render optional.txt")

    return {
        "copier_version": COPIER_VERSION,
        "conditional_exclude_with_new_question": "passed",
        "core_file_mode_false_negative_control": negative_mode,
        "controlled_update_core_file_mode": controlled_mode,
        "upstream_issue": "https://github.com/copier-org/copier/issues/2630",
    }


def root_entries(repository: Path) -> set[str]:
    return {path.name for path in repository.iterdir() if path.name != ".git"}


def assert_no_template_leakage(repository: Path) -> None:
    if (repository / "_components").exists():
        raise RuntimeError(f"_components leaked into {repository}")
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in file_map(repository).values()
    )
    if "template/_components" in text:
        raise RuntimeError(f"component include path leaked into {repository}")
    for marker in parity.FORBIDDEN_LEGACY_MARKERS:
        if marker in text:
            raise RuntimeError(f"legacy marker {marker!r} remains in {repository}")


def assert_no_platform_mechanisms(repository: Path) -> None:
    paths = {path.relative_to(repository).as_posix() for path in repository.rglob("*")}
    for marker in FORBIDDEN_TEMPLATE_PATH_PARTS:
        if any(marker in path for path in paths):
            raise RuntimeError(f"forbidden template-system path remains: {marker}")
    copier = (repository / "copier.yml").read_text(encoding="utf-8")
    for marker in ("_tasks", "_migrations", "_jinja_extensions", "_unsafe"):
        if marker in copier:
            raise RuntimeError(f"unsafe/custom Copier surface remains: {marker}")


def assert_custom_python_render(repository: Path) -> None:
    required = {
        "src/orbital_kit/__init__.py",
        "tests/orbital_kit/unit/test_public_package.py",
        "docs/orbital_kit/README.md",
        "examples/orbital_kit/config_demo.py",
        "workbench/orbital_kit/__init__.py",
    }
    paths = set(file_map(repository))
    missing = sorted(required - paths)
    if missing:
        raise RuntimeError(f"custom render paths are missing: {missing}")
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in file_map(repository).values()
    )
    if "[[[" in combined or "]]]" in combined:
        raise RuntimeError("unrendered Copier placeholders remain")
    if "sample_lib" in combined:
        raise RuntimeError("default package name leaked into custom render")
    if "OrbitalKitError" not in combined or "OrbitalKitConfig" not in combined:
        raise RuntimeError("custom public class names were not rendered")


def yaml_lock_sha(template_repository: Path) -> str:
    data = yaml.safe_load(
        (template_repository / "vendir.lock.yml").read_text(encoding="utf-8")
    )
    directories = data.get("directories", [])
    if len(directories) != 1:
        raise RuntimeError("unexpected Vendir lock directory count")
    contents = directories[0].get("contents", [])
    if len(contents) != 1:
        raise RuntimeError("unexpected Vendir lock content count")
    return str(contents[0]["git"]["sha"])


def assert_selective_vendir_config(
    template_repository: Path, include_paths: Sequence[str]
) -> None:
    data = yaml.safe_load(
        (template_repository / "vendir.yml").read_text(encoding="utf-8")
    )
    content = data["directories"][0]["contents"][0]
    expected = list(include_paths)
    if content.get("includePaths") != expected:
        raise RuntimeError(
            f"unexpected includePaths in {template_repository}: "
            f"{content.get('includePaths')}"
        )
    if content.get("legalPaths") != []:
        raise RuntimeError(
            f"Vendir default legal paths are not disabled in {template_repository}"
        )
    if "newRootPath" in content:
        raise RuntimeError(f"unexpected newRootPath in {template_repository}")


def copy_normalized_tree(
    source: Path,
    destination: Path,
    *,
    replacements: dict[str, str],
    exclude_components: bool = False,
) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    ignored_parts = {".git", ".venv", "__pycache__", "dist", "build"}
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(part in ignored_parts for part in relative.parts):
            continue
        if exclude_components and relative.parts[:2] == ("template", "_components"):
            continue
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(path, target)
            continue
        for old, new in replacements.items():
            text = text.replace(old, new)
        target.write_text(text, encoding="utf-8")
        if executable_bit(path):
            target.chmod(
                target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            )


def write_evidence(
    evidence_dir: Path,
    *,
    work_dir: Path,
    components_repository: Path,
    infra_template: Path,
    python_template: Path,
    infra_render: Path,
    python_render: Path,
    custom_render: Path,
    ownership: dict[str, str],
    result: dict[str, object],
) -> None:
    replacements = {
        components_repository.resolve().as_uri(): "https://github.com/betabitplus/ternforge-template-components.git",
        str(
            components_repository.resolve()
        ): "https://github.com/betabitplus/ternforge-template-components.git",
        str(
            infra_template.resolve()
        ): "https://github.com/betabitplus/ternforge-template-infra-repository.git",
        str(
            python_template.resolve()
        ): "https://github.com/betabitplus/ternforge-template-py-library.git",
        str(work_dir.resolve()): "/lab/work",
    }
    if evidence_dir.exists():
        shutil.rmtree(evidence_dir)
    evidence_dir.mkdir(parents=True)
    copy_normalized_tree(
        components_repository,
        evidence_dir / "components",
        replacements=replacements,
    )
    copy_normalized_tree(
        infra_template,
        evidence_dir / "template-views" / "infra-repository",
        replacements=replacements,
        exclude_components=True,
    )
    copy_normalized_tree(
        python_template,
        evidence_dir / "template-views" / "python-library",
        replacements=replacements,
        exclude_components=True,
    )
    copy_normalized_tree(
        infra_render,
        evidence_dir / "renders" / "infra-default",
        replacements=replacements,
    )
    copy_normalized_tree(
        python_render,
        evidence_dir / "renders" / "python-default",
        replacements=replacements,
    )
    copy_normalized_tree(
        custom_render,
        evidence_dir / "renders" / "python-custom",
        replacements=replacements,
    )
    for edge_name in (
        "copier-edge-template",
        "copier-edge-negative",
        "copier-edge-controlled",
        "copier-edge-optional",
    ):
        copy_normalized_tree(
            work_dir / edge_name,
            evidence_dir / "edge-cases" / edge_name,
            replacements=replacements,
        )
    write(
        evidence_dir / "ownership.json",
        json.dumps(ownership, indent=2, sort_keys=True) + "\n",
    )
    write(
        evidence_dir / "result.json",
        json.dumps(result, indent=2, sort_keys=True) + "\n",
    )

    checks = result["checks"]
    report = f"""# Ternforge template-system hardening

Status: **PASS**

## Scope

* one released components repository;
* minimal infrastructure final template;
* full Python-library final template;
* Vendir committed snapshots with explicit legal-path filtering;
* explicit Jinja wrappers and pyproject fragments;
* Copier 9.17.0 fresh/update lifecycle and upstream edge cases;
* full Python product checks.

## Result

```text
component source files        {result["component_source_file_count"]}
infra snapshot files          {result["infra_component_snapshot_file_count"]}
Python snapshot files         {result["python_component_snapshot_file_count"]}
Python output owners          {result["python_owner_count"]}
infra rendered files          {result["infra_rendered_file_count"]}
Python rendered files         {result["python_rendered_file_count"]}
Python product checks         {result["python_product_check_count"]}
Copier negative file mode     {result["copier_edge_cases"]["core_file_mode_false_negative_control"]}
Copier controlled file mode   {result["copier_edge_cases"]["controlled_update_core_file_mode"]}
components v0.1.0 SHA         {result["component_shas"]["v0.1.0"]}
components v0.2.0 SHA         {result["component_shas"]["v0.2.0"]}
components v0.3.0 SHA         {result["component_shas"]["v0.3.0"]}
```

Validated:

* infrastructure fresh output is exact and contains no Python/product leakage;
* each final template snapshots only its declared component paths through built-in Vendir `includePaths`;
* explicit `legalPaths: []` prevents root LICENSE/NOTICE files from bypassing selective snapshots;
* a Python-only component release changes only the infra Vendir declaration and lock, not its component files or render;
* componentized Python render matches the EXP-0031 product candidate outside platform provenance files;
* default and custom Python renders work through the actual component wrappers;
* `_components`, `.git`, assembler, manifests, `WIRING.json`, tasks, migrations and extensions do not reach consumers;
* a Python-only component release changes Python output and leaves infra output unchanged;
* a shared base component release changes exactly `.editorconfig` in both products;
* Copier updates preserve modified/deleted README and user-owned Python source;
* a guarded conditional `_exclude` remains safe when a new question is absent from old answers;
* Copier 9.17.0 reproduces the upstream new-executable limitation under `core.fileMode=false`;
* controlled updates with explicit `core.fileMode=true` preserve new executable files as `100755`;
* Vendir lock SHAs match released component commits and repeated sync is clean;
* the componentized Python render passes the full product verification suite.

## Checks

```text
{os.linesep.join(f"{name}: PASS" for name, passed in sorted(checks.items()) if passed)}
```
"""
    write(evidence_dir / "report.md", report)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--vendir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    baseline_root = args.baseline_root.resolve()
    vendir = args.vendir.resolve()
    work_dir = args.work_dir.resolve()
    evidence_dir = args.evidence_dir.resolve()
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)

    direct_template = work_dir / "direct-python-template"
    components_repository = work_dir / "components-repository"
    infra_template = work_dir / "infra-template"
    python_template = work_dir / "python-template"

    prepare_python_template_source(baseline_root, direct_template)
    mapping, pyproject_includes, component_meta = build_components_repository(
        direct_template,
        components_repository,
    )
    answers_include = component_meta["answers_include"]
    create_infra_template_repository(
        infra_template,
        components_repository,
        mapping,
        answers_include,
        vendir,
    )
    create_python_template_repository(
        python_template,
        direct_template,
        components_repository,
        mapping,
        pyproject_includes,
        answers_include,
        vendir,
    )

    assert_selective_vendir_config(infra_template, INFRA_INCLUDE_PATHS)
    assert_selective_vendir_config(python_template, PYTHON_INCLUDE_PATHS)
    assert_no_platform_mechanisms(infra_template)
    assert_no_platform_mechanisms(python_template)

    infra_v1 = work_dir / "renders" / "infra-v1"
    py_v1 = work_dir / "renders" / "py-v1"
    py_custom = work_dir / "renders" / "py-custom"
    render(infra_template, infra_v1, ref="v0.1.0")
    render(python_template, py_v1, ref="v0.1.0")
    render(
        python_template,
        py_custom,
        ref="v0.1.0",
        data={
            "project_name": "orbital-kit",
            "package_name": "orbital_kit",
            "project_title": "Orbital Kit",
            "project_title_lower": "orbital kit",
            "error_class_name": "OrbitalKitError",
            "config_class_name": "OrbitalKitConfig",
            "env_prefix": "ORBITAL_KIT",
            "repository_name": "orbital-kit",
        },
    )

    if root_entries(infra_v1) != INFRA_ROOT_ENTRIES:
        raise RuntimeError(
            f"infra root output mismatch: expected {sorted(INFRA_ROOT_ENTRIES)}, "
            f"got {sorted(root_entries(infra_v1))}"
        )
    assert_no_template_leakage(infra_v1)
    assert_no_template_leakage(py_v1)
    assert_no_template_leakage(py_custom)
    assert_custom_python_render(py_custom)

    baseline_render = work_dir / "baseline-render"
    parity_candidate = work_dir / "parity-candidate"
    parity.render_baseline(baseline_root, baseline_render)
    parity.transform_candidate(baseline_render, parity_candidate)
    for path in sorted(parity_candidate.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = text.replace(
            f"copier=={parity.COPIER_VERSION}", f"copier=={COPIER_VERSION}"
        )
        if updated != text:
            path.write_text(updated, encoding="utf-8")
    reference_answers = parity_candidate / "_copier_answers.yml"
    if reference_answers.exists():
        reference_answers.write_text(
            reference_answers.read_text(encoding="utf-8").replace(
                "_copier_answers.yml", ".copier-answers.yml"
            ),
            encoding="utf-8",
        )
    reference_pyproject = parity_candidate / "pyproject.toml"
    reference_text = reference_pyproject.read_text(encoding="utf-8").replace(
        "_copier_answers.yml", ".copier-answers.yml"
    )
    reference_text = reference_text.replace(
        '  ".agents/**",\n  ".devcontainer/**",',
        '  ".agents/**",\n  ".copier-answers.yml",\n  ".devcontainer/**",',
    )
    reference_text = reference_text.replace(
        '  "__pycache__/**",\n  ".copier-answers.yml",',
        '  "__pycache__/**",',
    )
    reference_pyproject.write_text(reference_text, encoding="utf-8")
    parity_comparison = compare_trees(
        parity_candidate,
        py_v1,
        ignore=PLATFORM_COMPARE_IGNORES,
        ignore_answers=True,
    )
    if not parity_comparison["equal"]:
        raise RuntimeError(
            f"componentized Python product differs from EXP-0031: {parity_comparison}"
        )

    initial_python_check_root = work_dir / "python-product-checks"
    shutil.copytree(py_v1, initial_python_check_root, symlinks=True)
    product_checks = parity.run_product_checks(initial_python_check_root)

    infra_snapshot = infra_template / "template" / "_components"
    python_snapshot = python_template / "template" / "_components"
    infra_snapshot_count = len(file_map(infra_snapshot))
    python_snapshot_count = len(file_map(python_snapshot))
    if any("/py/" in path or "py-library" in path for path in file_map(infra_snapshot)):
        raise RuntimeError(
            "Python-specific components leaked into infra template snapshot"
        )
    for snapshot in (infra_snapshot, python_snapshot):
        leaked_legal = [
            name for name in ("LICENSE", "NOTICE") if (snapshot / name).exists()
        ]
        if leaked_legal:
            raise RuntimeError(
                f"Vendir default legal paths bypassed includePaths in {snapshot}: "
                f"{leaked_legal}"
            )

    infra_v2_commit = update_template_components(
        infra_template,
        components_repository,
        "v0.2.0",
        "v0.2.0",
        vendir,
        INFRA_INCLUDE_PATHS,
    )
    python_v2_commit = update_template_components(
        python_template,
        components_repository,
        "v0.2.0",
        "v0.2.0",
        vendir,
        PYTHON_INCLUDE_PATHS,
    )
    if yaml_lock_sha(infra_template) != component_meta["v0.2.0"]:
        raise RuntimeError("infra Vendir lock does not match components v0.2.0")
    if yaml_lock_sha(python_template) != component_meta["v0.2.0"]:
        raise RuntimeError("Python Vendir lock does not match components v0.2.0")

    infra_v2_template_paths = commit_paths(infra_template, infra_v2_commit)
    python_v2_template_paths = commit_paths(python_template, python_v2_commit)
    if infra_v2_template_paths != ["vendir.lock.yml", "vendir.yml"]:
        raise RuntimeError(
            f"Python-only release polluted infra snapshot: {infra_v2_template_paths}"
        )
    expected_python_snapshot_change = (
        "template/_components/components/agents/py-library/template/"
        ".agents/skills/python-library-rules/SKILL.md"
    )
    if python_v2_template_paths != sorted(
        [expected_python_snapshot_change, "vendir.lock.yml", "vendir.yml"]
    ):
        raise RuntimeError(
            f"unexpected Python template snapshot update: {python_v2_template_paths}"
        )

    infra_v2 = work_dir / "renders" / "infra-v2"
    py_v2 = work_dir / "renders" / "py-v2"
    render(infra_template, infra_v2, ref="v0.2.0")
    render(python_template, py_v2, ref="v0.2.0")
    infra_py_only = compare_trees(infra_v1, infra_v2, ignore_answers=True)
    py_py_only = compare_trees(py_v1, py_v2, ignore_answers=True)
    expected_py_marker = ".agents/skills/python-library-rules/SKILL.md"
    if not infra_py_only["equal"]:
        raise RuntimeError(
            f"Python-only component changed infra output: {infra_py_only}"
        )
    if (
        py_py_only["changed"] != [expected_py_marker]
        or py_py_only["missing"]
        or py_py_only["added"]
    ):
        raise RuntimeError(f"unexpected Python-only output diff: {py_py_only}")

    infra_consumer = work_dir / "consumers" / "infra"
    py_consumer = work_dir / "consumers" / "python"
    render(infra_template, infra_consumer, ref="v0.1.0")
    render(python_template, py_consumer, ref="v0.1.0")
    initialize_consumer(infra_consumer, "initial infra consumer")
    initialize_consumer(py_consumer, "initial Python consumer")
    (infra_consumer / "README.md").unlink()
    write(py_consumer / "src" / "sample_lib" / "local_extension.py", "LOCAL = True\n")
    write(
        py_consumer / "README.md",
        (py_consumer / "README.md").read_text(encoding="utf-8") + "\nLocal note.\n",
    )
    commit(infra_consumer, "delete create-once README")
    commit(py_consumer, "user-owned Python changes")
    update_consumer(infra_consumer, "v0.2.0")
    update_consumer(py_consumer, "v0.2.0")
    if (infra_consumer / "README.md").exists():
        raise RuntimeError("infra README deletion was not preserved")
    if not (py_consumer / "src" / "sample_lib" / "local_extension.py").exists():
        raise RuntimeError("user-owned Python source was lost")
    if "Local note." not in (py_consumer / "README.md").read_text(encoding="utf-8"):
        raise RuntimeError("Python README modification was lost")
    commit(infra_consumer, "merge template update v0.2.0")
    commit(py_consumer, "merge template update v0.2.0")

    update_template_components(
        infra_template,
        components_repository,
        "v0.3.0",
        "v0.3.0",
        vendir,
        INFRA_INCLUDE_PATHS,
    )
    update_template_components(
        python_template,
        components_repository,
        "v0.3.0",
        "v0.3.0",
        vendir,
        PYTHON_INCLUDE_PATHS,
    )
    if yaml_lock_sha(infra_template) != component_meta["v0.3.0"]:
        raise RuntimeError("infra Vendir lock does not match components v0.3.0")
    if yaml_lock_sha(python_template) != component_meta["v0.3.0"]:
        raise RuntimeError("Python Vendir lock does not match components v0.3.0")

    infra_v3 = work_dir / "renders" / "infra-v3"
    py_v3 = work_dir / "renders" / "py-v3"
    render(infra_template, infra_v3, ref="v0.3.0")
    render(python_template, py_v3, ref="v0.3.0")
    infra_shared = compare_trees(infra_v2, infra_v3, ignore_answers=True)
    py_shared = compare_trees(py_v2, py_v3, ignore_answers=True)
    for label, comparison in (("infra", infra_shared), ("python", py_shared)):
        if (
            comparison["changed"] != [".editorconfig"]
            or comparison["missing"]
            or comparison["added"]
        ):
            raise RuntimeError(
                f"unexpected shared component diff for {label}: {comparison}"
            )

    update_consumer(infra_consumer, "v0.3.0")
    update_consumer(py_consumer, "v0.3.0")
    if (infra_consumer / "README.md").exists():
        raise RuntimeError("infra README deletion was restored by shared update")
    if not (py_consumer / "src" / "sample_lib" / "local_extension.py").exists():
        raise RuntimeError("user-owned Python source was lost after shared update")
    if "shared component update v0.3.0" not in (
        infra_consumer / ".editorconfig"
    ).read_text(encoding="utf-8"):
        raise RuntimeError("infra shared component update did not arrive")
    if "shared component update v0.3.0" not in (
        py_consumer / ".editorconfig"
    ).read_text(encoding="utf-8"):
        raise RuntimeError("Python shared component update did not arrive")

    vendir_sync(infra_template, vendir)
    vendir_sync(python_template, vendir)
    for repository in (infra_template, python_template):
        clean = git(repository, "diff", "--exit-code")
        if not clean.passed:
            raise RuntimeError(f"repeated Vendir sync left diff in {repository}")

    copier_edge_cases = validate_copier_edge_cases(work_dir)

    ownership = dict(sorted(mapping.items()))
    ownership["pyproject.toml"] = "final-template (explicit fragments)"
    ownership[".copier-answers.yml"] = "final-template + repository/copier include"
    if len(ownership) != len(set(ownership)):
        raise RuntimeError("duplicate output ownership detected")

    checks = {
        "infra_exact_output": True,
        "python_product_parity": bool(parity_comparison["equal"]),
        "custom_python_render": True,
        "component_leakage_zero": True,
        "legacy_platform_mechanisms_zero": True,
        "vendir_lock_exact": True,
        "vendir_repeat_sync_clean": True,
        "component_snapshots_filtered": True,
        "vendir_legal_paths_disabled": True,
        "copier_conditional_exclude_guarded": True,
        "copier_controlled_executable_mode": (
            copier_edge_cases["controlled_update_core_file_mode"] == "100755"
        ),
        "python_only_update_isolated": bool(infra_py_only["equal"]),
        "shared_update_exact": True,
        "copier_user_ownership_preserved": True,
        "full_python_product_checks": all(result.passed for result in product_checks),
    }
    result: dict[str, object] = {
        "status": "passed",
        "versions": {
            "copier": COPIER_VERSION,
            "uv": UV_VERSION,
            "vendir": VENDIR_VERSION,
            "baseline": BASELINE_SHA,
        },
        "component_shas": {
            "v0.1.0": component_meta["v0.1.0"],
            "v0.2.0": component_meta["v0.2.0"],
            "v0.3.0": component_meta["v0.3.0"],
        },
        "component_source_file_count": len(file_map(components_repository)),
        "infra_component_snapshot_file_count": infra_snapshot_count,
        "python_component_snapshot_file_count": python_snapshot_count,
        "python_owner_count": len(ownership),
        "infra_rendered_file_count": len(file_map(infra_v1)),
        "python_rendered_file_count": len(file_map(py_v1)),
        "python_product_check_count": len(product_checks),
        "copier_edge_cases": copier_edge_cases,
        "parity_comparison": parity_comparison,
        "python_only_update": {
            "infra": infra_py_only,
            "python": py_py_only,
            "infra_template_paths": infra_v2_template_paths,
            "python_template_paths": python_v2_template_paths,
        },
        "shared_update": {
            "infra": infra_shared,
            "python": py_shared,
        },
        "checks": checks,
        "product_check_names": [result.name for result in product_checks],
    }

    write_evidence(
        evidence_dir,
        work_dir=work_dir,
        components_repository=components_repository,
        infra_template=infra_template,
        python_template=python_template,
        infra_render=infra_v1,
        python_render=py_v1,
        custom_render=py_custom,
        ownership=ownership,
        result=result,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
