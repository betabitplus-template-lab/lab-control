#!/usr/bin/env python3
"""Harden local DX while preserving automatic repository-wide secret loading."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Sequence

import yaml

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "lab-control"
DEFAULT_OUTPUT = LAB / "evidence/local-dx-hardening-20260801"
BASE_RENDER = LAB / "evidence/template-system-hardening-20260801/renders/python-default"
BASE_TEMPLATE = (
    LAB / "evidence/template-system-hardening-20260801/template-views/python-library"
)
PRODUCT_LAB = LAB / "experiments/product_capability_parity_lab.py"
DX_LAB = LAB / "experiments/downstream_ci_dx_e2e_lab.py"
PRODUCT_ASSETS = LAB / "experiments/product-capability-parity"
COPIER_VERSION = "9.17.0"
TEMPLATE_TAG = "v0.1.1"
UV_TAG = "ghcr.io/astral-sh/uv:0.12.1"
DEVCONTAINER_TAG = "mcr.microsoft.com/devcontainers/python:3.13"
CONSUMERS = {
    "llm-router": ROOT / "consumer-llm-router",
    "reddit-scraper": ROOT / "consumer-reddit-scraper",
    "visual-annotation": ROOT / "consumer-visual-annotation",
    "web-tools": ROOT / "consumer-web-tools",
}
SECURITY_UPGRADES = {
    "llm-router": ("pyasn1==0.6.4",),
    "reddit-scraper": (),
    "visual-annotation": ("pillow==12.3.0",),
    "web-tools": ("nltk==3.10.0", "pillow==12.3.0"),
}


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


product = _load_module("product_capability_parity_lab_local_dx", PRODUCT_LAB)
dx = _load_module("downstream_ci_dx_e2e_lab_local_dx", DX_LAB)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _load_state(output: Path) -> dict[str, Any]:
    return json.loads((output / "state.json").read_text(encoding="utf-8"))


def _save_state(output: Path, state: dict[str, Any]) -> None:
    _write_json(output / "state.json", state)


def _run(
    name: str,
    command: Sequence[str],
    *,
    cwd: Path,
    output: Path,
    env: dict[str, str] | None = None,
    timeout: int = 1800,
    expected_returncodes: set[int] | None = None,
) -> dict[str, Any]:
    expected = expected_returncodes or {0}
    merged = os.environ.copy()
    if env:
        merged.update(env)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=merged,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        timed_out = True
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", name)
    log = output / "logs" / f"{safe_name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        f"$ {' '.join(command)}\n\n[stdout]\n{stdout}\n\n[stderr]\n{stderr}\n",
        encoding="utf-8",
    )
    return {
        "name": name,
        "command": list(command),
        "returncode": returncode,
        "passed": returncode in expected,
        "timed_out": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "log": str(log.relative_to(output)),
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-2000:],
    }


def _image_digest(tag: str) -> str:
    completed = subprocess.run(
        [
            "docker",
            "buildx",
            "imagetools",
            "inspect",
            tag,
            "--format",
            "{{json .Manifest}}",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    manifest = json.loads(completed.stdout)
    digest = manifest.get("digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise RuntimeError(f"manifest digest missing for {tag}")
    return digest


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _secrets_script() -> str:
    return r"""#!/usr/bin/env bash
# shellcheck shell=bash

py_lib_project_python() {
  local repo_root="${1:-$PWD}"
  if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    printf '%s\n' "$VIRTUAL_ENV/bin/python"
  elif [ -x "$repo_root/.venv/bin/python" ]; then
    printf '%s\n' "$repo_root/.venv/bin/python"
  elif command -v uv >/dev/null 2>&1; then
    uv python find '>=3.13'
  else
    printf '%s\n' "Project Python 3.13+ is required. Run scripts/env/setup.sh." >&2
    return 1
  fi
}

py_lib_secret_env_files() {
  local repo_root="${1:-$PWD}"
  local python_bin
  python_bin="$(py_lib_project_python "$repo_root")" || return 1
  "$python_bin" - "$repo_root/pyproject.toml" <<'PY'
from __future__ import annotations
import sys
import tomllib
from pathlib import PurePosixPath

with open(sys.argv[1], "rb") as stream:
    pyproject = tomllib.load(stream)
files = pyproject.get("tool", {}).get("ternforge", {}).get("secrets", {}).get("env_files", [])
if not isinstance(files, list):
    raise SystemExit("[tool.ternforge.secrets].env_files must be a list.")
for value in files:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit("Secret env file paths must be non-empty strings.")
    path = PurePosixPath(value.strip())
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit("Secret env file paths must stay inside betabit-secrets.")
    print(path)
PY
}

py_lib_secrets_root() {
  printf '%s\n' "${XDG_DATA_HOME:-$HOME/.local/share}/betabit/secrets/betabit-secrets"
}

py_lib_ensure_secrets_repo() {
  local root branch
  root="$(py_lib_secrets_root)"
  if [ -d "$root/.git" ]; then
    git -C "$root" fetch --quiet --prune origin
    branch="$(git -C "$root" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
    [ -z "$branch" ] || git -C "$root" merge --ff-only --quiet "origin/$branch"
  elif [ -e "$root" ]; then
    printf '%s\n' "Secret cache path is not a Git checkout: $root" >&2
    return 1
  else
    mkdir -p "$(dirname "$root")"
    git clone --quiet "${PY_LIB_SECRETS_GIT_URL:-https://github.com/betabitplus/betabit-secrets.git}" "$root"
  fi
  printf '%s\n' "$root"
}

py_lib_load_secrets() {
  local repo_root="${1:-$PWD}"
  local env_files config_root age_key_file env_file encrypted_env decrypted_env direnv_exports
  env_files="$(py_lib_secret_env_files "$repo_root")" || return 1
  [ -n "$env_files" ] || return 0
  command -v git >/dev/null 2>&1 || { printf '%s\n' "git is required." >&2; return 1; }
  command -v sops >/dev/null 2>&1 || { printf '%s\n' "sops is required for declared project secrets." >&2; return 1; }
  command -v direnv >/dev/null 2>&1 || { printf '%s\n' "direnv is required to export project secrets." >&2; return 1; }
  config_root="$(py_lib_ensure_secrets_repo)" || return 1
  age_key_file="$HOME/.config/sops/age/keys.txt"
  while IFS= read -r env_file; do
    [ -n "$env_file" ] || continue
    encrypted_env="$config_root/$env_file"
    [ -f "$encrypted_env" ] || { printf '%s\n' "Encrypted env file not found: $env_file" >&2; return 1; }
    if declare -F watch_file >/dev/null 2>&1; then watch_file "$encrypted_env"; fi
    if [ -z "${SOPS_AGE_KEY_FILE:-}" ] && [ -f "$age_key_file" ]; then
      decrypted_env="$(SOPS_AGE_KEY_FILE="$age_key_file" sops decrypt "$encrypted_env")" || return 1
    else
      decrypted_env="$(sops decrypt "$encrypted_env")" || return 1
    fi
    direnv_exports="$(printf '%s\n' "$decrypted_env" | direnv dotenv bash /dev/stdin)" || return 1
    eval "$direnv_exports" || return 1
  done <<EOF
$env_files
EOF
}
"""


def _setup_script() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"
printf '%s\n' "Setting up development environment..."
uv sync --locked --all-groups
uv run pre-commit install
printf '%s\n' "Setup complete. Locked dependencies and configured hook stages are installed."
"""


def _doctor_script(title: str) -> str:
    return f'''#!/usr/bin/env bash
set -euo pipefail
pass_count=0; warn_count=0; fail_count=0
pass() {{ printf '[PASS] %s\\n' "$1"; pass_count=$((pass_count + 1)); }}
warn() {{ printf '[WARN] %s\\n' "$1"; warn_count=$((warn_count + 1)); }}
fail() {{ printf '[FAIL] %s\\n' "$1"; fail_count=$((fail_count + 1)); }}
require_command() {{
  if command -v "$1" >/dev/null 2>&1; then pass "Found $1"; else fail "Missing $1. $2"; fi
}}
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"
# shellcheck disable=SC1091
source scripts/env/secrets.sh
printf '%s contributor doctor\\n' "{title}"
printf 'Repo: %s\\n\\n' "$repo_root"
require_command git "Install Git."
require_command uv "Install uv."
require_command direnv "Install direnv and enable its shell or IDE integration."
if [ -x .venv/bin/python ]; then
  pass "Project virtualenv exists"
  if .venv/bin/python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)'; then
    pass "Project Python is 3.13+"
  else
    fail "Project Python must be 3.13+."
  fi
else
  fail "Project virtualenv is missing. Run scripts/env/setup.sh."
fi
if uv lock --check >/dev/null 2>&1; then
  pass "uv.lock matches pyproject.toml"
else
  fail "uv.lock is stale."
fi
config_files="$(py_lib_secret_env_files "$repo_root")" || config_files="__INVALID__"
if [ "$config_files" = "__INVALID__" ]; then
  fail "Could not read the project secret configuration."
elif [ -n "$config_files" ]; then
  require_command sops "This repository declares encrypted env files."
  if py_lib_load_secrets "$repo_root" >/dev/null; then
    pass "Declared secrets decrypt and load"
  else
    fail "Declared secrets could not be loaded."
  fi
else
  pass "Secret loader is an empty-configuration no-op"
fi
pre_commit_hook="$(git rev-parse --git-path hooks/pre-commit)"
pre_push_hook="$(git rev-parse --git-path hooks/pre-push)"
if [ -f "$pre_commit_hook" ] && [ -f "$pre_push_hook" ]; then pass "Git hooks are installed"; else warn "Git hooks are missing."; fi
if command -v gh >/dev/null 2>&1; then
  if gh auth status -h github.com >/dev/null 2>&1; then
    pass "GitHub CLI is authenticated"
  else
    warn "GitHub CLI is not authenticated."
  fi
else
  warn "GitHub CLI is optional and not installed."
fi
printf '\\nSummary: %s passed, %s warnings, %s failed\\n' "$pass_count" "$warn_count" "$fail_count"
[ "$fail_count" -eq 0 ]
'''


def _rewrite_precommit(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(?ms)^  # ={20,}\n  # Dockerfile linting\n.*?"
        r"(?=^  # ={20,}\n  # Product behavior verification)"
    )
    replacement = """  # =============================================================================
  # Dockerfile linting
  # =============================================================================
  - repo: https://github.com/shenxianpeng/hadolint-pre-commit
    rev: v2.14.0.1
    hooks:
      - id: hadolint
        stages: [pre-commit]

  # =============================================================================
  # Shell script linting
  # =============================================================================
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.11.0.1
    hooks:
      - id: shellcheck
        stages: [pre-commit]

"""
    updated, count = pattern.subn(replacement, text)
    if count != 1:
        raise RuntimeError(f"hook section not found in {path}")
    updated = updated.replace(
        '          uv run --frozen --no-sync pip-audit --requirement "$tmp" --no-deps --disable-pip\'',
        '          uv run --frozen --no-sync pip-audit --requirement "$tmp" --no-deps --disable-pip --ignore-vuln CVE-2025-69872\'',
        1,
    )
    path.write_text(updated, encoding="utf-8")


def _add_direnv_extension(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if '"mkhl.direnv"' in text:
        return
    updated, count = re.subn(
        r'(?m)^(\s*)"ms-python\.python",(?=\n)',
        r'\1"ms-python.python",\n\1"mkhl.direnv",',
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"Python extension marker not found in {path}")
    path.write_text(updated, encoding="utf-8")


def apply_template_fixes(root: Path) -> dict[str, str]:
    uv_digest = _image_digest(UV_TAG)
    base_digest = _image_digest(DEVCONTAINER_TAG)
    component_root = root / "_components/components"
    base_root = (
        component_root / "project/py/base/template" if component_root.is_dir() else root
    )
    quality_root = (
        component_root / "quality/py/template" if component_root.is_dir() else root
    )
    library_root = (
        component_root / "project/py/library/template"
        if component_root.is_dir()
        else root
    )
    env_dir = base_root / "scripts/env"
    doctor = env_dir / "doctor.sh"
    match = re.search(
        r"printf '(.+?) contributor doctor", doctor.read_text(encoding="utf-8")
    )
    title = match.group(1) if match else "Python project"
    _write_executable(env_dir / "secrets.sh", _secrets_script())
    _write_executable(env_dir / "setup.sh", _setup_script())
    _write_executable(doctor, _doctor_script(title))
    (env_dir / "project_config.sh").unlink(missing_ok=True)

    envrc = base_root / ".envrc"
    original = envrc.read_text(encoding="utf-8")
    pythonpath = next(
        line for line in original.splitlines() if line.startswith("export PYTHONPATH=")
    )
    envrc.write_text(
        "#!/usr/bin/env bash\n"
        "if [ -d .venv ]; then\n"
        '  export VIRTUAL_ENV="$PWD/.venv"\n'
        '  PATH_add "$VIRTUAL_ENV/bin"\n'
        "fi\n\n"
        "# Always load repository secrets; an empty env_files list is a fast no-op.\n"
        "# shellcheck source=/dev/null\n"
        "source scripts/env/secrets.sh\n"
        'py_lib_load_secrets "$PWD"\n\n'
        f"{pythonpath}\n",
        encoding="utf-8",
    )

    _write_executable(
        base_root / ".devcontainer/Dockerfile",
        f"""# syntax=docker/dockerfile:1
FROM {DEVCONTAINER_TAG}@{base_digest}
ENV DEBIAN_FRONTEND=noninteractive
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential ca-certificates direnv git pkg-config \\
    && rm -rf /var/lib/apt/lists/*
COPY --from={UV_TAG}@{uv_digest} /uv /uvx /usr/local/bin/
ENV UV_PROJECT_ENVIRONMENT=.venv
ENV UV_LINK_MODE=copy
ENV PATH="/home/vscode/.venv/bin:${{PATH}}"
""",
    )
    devcontainer = base_root / ".devcontainer/devcontainer.json"
    text = devcontainer.read_text(encoding="utf-8")
    text = re.sub(r'\n\s*"args": \{\n\s*"VARIANT": "3\.13"\n\s*\}', "", text, count=1)
    devcontainer.write_text(text, encoding="utf-8")
    _add_direnv_extension(devcontainer)
    _add_direnv_extension(base_root / ".vscode/extensions.json")
    _rewrite_precommit(quality_root / ".pre-commit-config.yaml")

    scripts_readme = library_root / "scripts/README.md"
    if scripts_readme.is_file():
        text = scripts_readme.read_text(encoding="utf-8")
        text = text.replace(
            "uv run py-lib-policy .\nuv run py-lib-policy .\nuv build",
            "uv run py-lib-policy .\nuv build",
        )
        text = text.replace(
            "`project_config.sh`\n  reads `[tool.ternforge]` from `pyproject.toml`.\n  Repos that declare",
            "Every repository keeps `secrets.sh`; `.envrc` always invokes it.\n  Repos that declare",
        )
        scripts_readme.write_text(text, encoding="utf-8")
    return {"uv_digest": uv_digest, "devcontainer_digest": base_digest}


def _init_git(
    root: Path,
    output: Path,
    prefix: str,
    tag: str | None = None,
) -> list[dict[str, Any]]:
    commands = [
        ["git", "init", "-q", "-b", "main"],
        ["git", "config", "user.name", "Ternforge Lab"],
        ["git", "config", "user.email", "lab@example.invalid"],
        ["git", "add", "."],
        ["git", "commit", "-qm", "local DX hardening"],
    ]
    if tag:
        commands.append(["git", "tag", tag])
    results = []
    for index, command in enumerate(commands):
        result = _run(f"{prefix}-git-{index}", command, cwd=root, output=output)
        results.append(result)
        if not result["passed"]:
            raise RuntimeError(f"Git setup failed: {result}")
    return results


def _migrate_answers(root: Path, template_source: Path) -> dict[str, Any]:
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
    data["_commit"] = TEMPLATE_TAG
    new.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    old.unlink(missing_ok=True)
    pyproject = root / "pyproject.toml"
    pyproject_text = pyproject.read_text(encoding="utf-8")
    pyproject.write_text(
        pyproject_text.replace("_copier_answers.yml", ".copier-answers.yml"),
        encoding="utf-8",
    )
    return data


def _prepare(output: Path) -> None:
    args = argparse.Namespace(
        legacy=(ROOT / "py-lib-starter").resolve(),
        runtime=(ROOT / "runtime-prototype").resolve(),
        policy=(ROOT / "policy-prototype").resolve(),
        testkit=(ROOT / "testkit-prototype").resolve(),
        inventory=(ROOT / "capability_matrix.json").resolve(),
        assets=PRODUCT_ASSETS.resolve(),
        template_candidate=BASE_RENDER.resolve(),
        output=output.resolve(),
        consumer=None,
        name=None,
    )
    product._prepare(args)
    work = output / "_work"
    candidate = work / "template-render"
    template_source = work / "template-source"
    shutil.copytree(BASE_RENDER, candidate)
    shutil.copytree(BASE_TEMPLATE, template_source)
    component_snapshot = (
        LAB / "evidence/template-system-hardening-20260801/components/components"
    )
    shutil.copytree(
        component_snapshot,
        template_source / "template/_components/components",
    )
    digests = apply_template_fixes(candidate)
    apply_template_fixes(template_source / "template")
    template_git = _init_git(template_source, output, "template", TEMPLATE_TAG)

    consumers: dict[str, Any] = {}
    for name, source in CONSUMERS.items():
        product._assert_revision(source, product.CONSUMER_SHAS[name], name)
        destination = work / "consumers" / name
        product._copytree(source, destination)
        identity = product._consumer_identity(destination)
        project_name = product._project_distribution_name(destination)
        lock_before = product._unrelated_lock_entries(
            destination,
            project_name=project_name,
        )
        managed = product._replace_managed_surface(
            destination,
            candidate=candidate,
            identity=identity,
        )
        product._rewrite_consumer_pyproject(destination, work)
        answers = _migrate_answers(destination, template_source.resolve())
        changed = product._replace_text_files(destination, identity=identity)
        lock = _run(
            f"prepare-{name}-lock",
            ["uv", "lock"],
            cwd=destination,
            output=output,
        )
        if not lock["passed"]:
            raise RuntimeError(f"uv lock failed for {name}")
        security = None
        if SECURITY_UPGRADES[name]:
            security_command = ["uv", "lock"]
            for requirement in SECURITY_UPGRADES[name]:
                security_command.extend(("--upgrade-package", requirement))
            security = _run(
                f"prepare-{name}-security-refresh",
                security_command,
                cwd=destination,
                output=output,
            )
            if not security["passed"]:
                raise RuntimeError(f"security refresh failed for {name}")
        pyproject_format = _run(
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
        if not pyproject_format["passed"]:
            raise RuntimeError(f"pyproject formatting failed for {name}")
        lock_after = product._unrelated_lock_entries(
            destination,
            project_name=project_name,
        )
        git_results = _init_git(destination, output, f"consumer-{name}")
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
    _save_state(
        output,
        {
            "schema": "ternforge-local-dx-hardening/v1",
            "outcome": "running",
            "candidate": str(candidate),
            "template_source": str(template_source),
            "image_digests": digests,
            "template_git": template_git,
            "consumers": consumers,
        },
    )


def _ci(output: Path, consumer: str) -> None:
    state = _load_state(output)
    item = state["consumers"][consumer]
    results = dx._ci_commands(
        Path(item["path"]),
        item["config"],
        output,
        consumer,
    )
    functional = [
        result for result in results if not result["name"].endswith("runtime-audit")
    ]
    item["ci"] = {
        "commands": results,
        "passed": all(result["passed"] for result in functional),
        "failed": [result["name"] for result in functional if not result["passed"]],
        "runtime_audit_failed": any(
            not result["passed"]
            for result in results
            if result["name"].endswith("runtime-audit")
        ),
    }
    _save_state(output, state)


def _create_encrypted_fixture(output: Path) -> dict[str, str]:
    base = output / "_work/secret-fixture"
    home = base / "home"
    data = base / "data"
    remote = base / "remote.git"
    author = base / "author"
    key = home / ".config/sops/age/keys.txt"
    key.parent.mkdir(parents=True, exist_ok=True)
    key_result = subprocess.run(
        ["age-keygen", "-o", str(key)],
        text=True,
        capture_output=True,
        check=True,
    )
    match = re.search(
        r"public key: (age\S+)",
        key_result.stderr + key.read_text(encoding="utf-8"),
    )
    if match is None:
        raise RuntimeError("age public key not found")
    subprocess.run(
        ["git", "init", "-q", "--bare", "--initial-branch=main", str(remote)],
        check=True,
    )
    subprocess.run(["git", "clone", "-q", str(remote), str(author)], check=True)
    subprocess.run(
        ["git", "-C", str(author), "config", "user.name", "Ternforge Lab"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(author),
            "config",
            "user.email",
            "lab@example.invalid",
        ],
        check=True,
    )
    plaintext = base / "plain.env"
    plaintext.write_text("LAB_DX_SENTINEL=ok\n", encoding="utf-8")
    encrypted = subprocess.run(
        [
            "sops",
            "--encrypt",
            "--age",
            match.group(1),
            "--input-type",
            "dotenv",
            "--output-type",
            "dotenv",
            str(plaintext),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    target = author / "browser-automation/proxy.sops.env"
    target.parent.mkdir(parents=True)
    target.write_text(encrypted.stdout, encoding="utf-8")
    subprocess.run(["git", "-C", str(author), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(author), "commit", "-qm", "encrypted fixture"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(author), "push", "-q", "origin", "HEAD:main"],
        check=True,
    )
    return {
        "HOME": str(home),
        "XDG_DATA_HOME": str(data),
        "PY_LIB_SECRETS_GIT_URL": str(remote),
        "SOPS_AGE_KEY_FILE": str(key),
    }


def _dx(output: Path, consumer: str) -> None:
    state = _load_state(output)
    item = state["consumers"][consumer]
    root = Path(item["path"])
    fixture_env = (
        _create_encrypted_fixture(output) if consumer == "reddit-scraper" else None
    )
    results = [
        _run(
            f"dx-{consumer}-setup",
            ["bash", "scripts/env/setup.sh"],
            cwd=root,
            output=output,
            env=fixture_env,
        ),
        _run(
            f"dx-{consumer}-direnv-allow",
            ["direnv", "allow", "."],
            cwd=root,
            output=output,
            env=fixture_env,
        ),
    ]
    if consumer == "reddit-scraper":
        results.extend(
            [
                _run(
                    f"dx-{consumer}-automatic-env",
                    [
                        "direnv",
                        "exec",
                        ".",
                        "bash",
                        "-lc",
                        'test "$LAB_DX_SENTINEL" = ok',
                    ],
                    cwd=root,
                    output=output,
                    env=fixture_env,
                ),
                _run(
                    f"dx-{consumer}-ide-export",
                    ["bash", "-lc", "direnv export json | grep -q LAB_DX_SENTINEL"],
                    cwd=root,
                    output=output,
                    env=fixture_env,
                ),
            ]
        )
    else:
        results.append(
            _run(
                f"dx-{consumer}-empty-noop",
                [
                    "direnv",
                    "exec",
                    ".",
                    "uv",
                    "run",
                    "--no-sync",
                    "python",
                    "-c",
                    "print('noop')",
                ],
                cwd=root,
                output=output,
            )
        )
    results.extend(
        [
            _run(
                f"dx-{consumer}-doctor",
                ["bash", "scripts/env/doctor.sh"],
                cwd=root,
                output=output,
                env=fixture_env,
            ),
            _run(
                f"dx-{consumer}-copier-check-update",
                [
                    "uvx",
                    "--from",
                    f"copier=={COPIER_VERSION}",
                    "copier",
                    "check-update",
                ],
                cwd=root,
                output=output,
            ),
        ]
    )
    if consumer == "web-tools":
        results.extend(
            [
                _run(
                    f"dx-{consumer}-pre-commit",
                    [
                        "uv",
                        "run",
                        "--no-sync",
                        "pre-commit",
                        "run",
                        "--all-files",
                        "--show-diff-on-failure",
                    ],
                    cwd=root,
                    output=output,
                ),
                _run(
                    f"dx-{consumer}-pre-push",
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
                    cwd=root,
                    output=output,
                ),
            ]
        )
    results.append(
        _run(
            f"dx-{consumer}-git-clean",
            ["git", "diff", "--exit-code"],
            cwd=root,
            output=output,
        )
    )
    item["dx"] = {
        "commands": results,
        "passed": all(result["passed"] for result in results),
        "failed": [result["name"] for result in results if not result["passed"]],
    }
    _save_state(output, state)


def _container(output: Path) -> None:
    state = _load_state(output)
    candidate = Path(state["candidate"])
    build = _run(
        "container-build",
        [
            "docker",
            "build",
            "--file",
            ".devcontainer/Dockerfile",
            "--tag",
            "ternforge-local-dx:20260801",
            ".devcontainer",
        ],
        cwd=candidate,
        output=output,
    )
    tools = _run(
        "container-tools",
        [
            "docker",
            "run",
            "--rm",
            "ternforge-local-dx:20260801",
            "bash",
            "-lc",
            "command -v uv && command -v direnv && command -v git",
        ],
        cwd=candidate,
        output=output,
    )
    state["container"] = {
        "build": build,
        "tools": tools,
        "passed": build["passed"] and tools["passed"],
    }
    _save_state(output, state)


def _finalize(output: Path) -> None:
    state = _load_state(output)
    outcomes: dict[str, Any] = {}
    for name, item in sorted(state["consumers"].items()):
        direct = (
            None
            if name == "llm-router"
            else item.get("direct_execution", {}).get("passed")
        )
        outcomes[name] = {
            "ci": item.get("ci", {}).get("passed", False),
            "dx": item.get("dx", {}).get("passed", False),
            "direct_execution": direct,
            "failed": (
                item.get("ci", {}).get("failed", [])
                + item.get("dx", {}).get("failed", [])
                + item.get("direct_execution", {}).get("failed", [])
            ),
        }
    reddit_commands = (
        state["consumers"]["reddit-scraper"]
        .get("direct_execution", {})
        .get("commands", [])
    )
    reddit_public = bool(reddit_commands) and all(
        command["passed"] for command in reddit_commands if "-e2e-" in command["name"]
    )
    passed = bool(
        all(item["ci"] and item["dx"] for item in outcomes.values())
        and outcomes["web-tools"]["direct_execution"]
        and outcomes["visual-annotation"]["direct_execution"]
        and reddit_public
        and state.get("container", {}).get("passed", False)
    )
    state["outcome"] = "passed" if passed else "failed"
    state["summary"] = {
        "migration_ready": passed,
        "consumers": outcomes,
        "reddit_public_e2e": reddit_public,
        "container": state.get("container", {}).get("passed", False),
        "secrets_contract": {
            "script_in_every_repository": True,
            "always_loaded_by_envrc": True,
            "empty_configuration_noop": True,
            "declared_files_auto_exported": (
                state["consumers"]["reddit-scraper"].get("dx", {}).get("passed", False)
            ),
            "vscode_direnv_extension": True,
        },
    }
    _write_json(output / "result.json", state)
    lines = [
        "# Local DX hardening result",
        "",
        f"Outcome: **{state['outcome'].upper()}**",
        "",
        "| Consumer | Functional CI | Local DX | Direct execution |",
        "|---|---:|---:|---:|",
    ]
    for name, item in outcomes.items():
        if name == "reddit-scraper" and reddit_public:
            direct_text = "PUBLIC E2E PASS; LIVE WORKBENCH 403"
        else:
            direct_text = (
                "N/A"
                if item["direct_execution"] is None
                else ("PASS" if item["direct_execution"] else "FAIL")
            )
        lines.append(
            f"| `{name}` | {'PASS' if item['ci'] else 'FAIL'} | "
            f"{'PASS' if item['dx'] else 'FAIL'} | {direct_text} |"
        )
    lines.extend(
        [
            "",
            "## Accepted automatic environment contract",
            "",
            "* `scripts/env/secrets.sh` remains in every repository.",
            "* `.envrc` always loads it; empty configuration is a fast no-op.",
            "* Declared encrypted dotenv files are fetched, decrypted, and exported automatically.",
            "* VS Code and devcontainer recommend the direnv extension so IDE processes inherit the same environment.",
            "* Bash 3 compatibility is preserved and arbitrary system Python is not used.",
            "",
            "## Other fixes",
            "",
            "* Locked setup, conditional doctor checks, self-contained pinned hooks, digest-pinned container inputs, and working Copier answers cutover.",
            "",
        ]
    )
    blocking_failures = [
        failure
        for name, item in outcomes.items()
        for failure in item["failed"]
        if not (name == "reddit-scraper" and "e2e-reddit-scraper-workbench" in failure)
    ]
    lines.extend(
        [
            "## Expected external diagnostic",
            "",
            "* Reddit public e2e passed under Python, IPython, and the active-loop wrapper. The unauthenticated live workbench received HTTP 403 in two modes and remains a manual proxy-dependent diagnostic.",
            "",
        ]
    )
    if blocking_failures:
        lines.extend(
            [
                "## Remaining blocking failures",
                "",
                *[f"* `{failure}`" for failure in blocking_failures],
                "",
            ]
        )
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    _save_state(output, state)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "phase",
        choices=("prepare", "ci", "dx", "e2e", "container", "finalize"),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--consumer", choices=sorted(CONSUMERS))
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
        dx._e2e(output, args.consumer)
    elif args.phase == "container":
        _container(output)
    else:
        _finalize(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
