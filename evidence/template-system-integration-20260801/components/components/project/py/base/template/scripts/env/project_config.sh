#!/usr/bin/env bash

py_lib_project_config_python() {
  if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    printf '%s\n' "$VIRTUAL_ENV/bin/python"
    return 0
  fi

  if [ -x ".venv/bin/python" ]; then
    printf '%s\n' ".venv/bin/python"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' "python3"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    printf '%s\n' "python"
    return 0
  fi

  return 1
}

py_lib_read_project_env_config() {
  local repo_root="$1"
  local python_bin
  python_bin="$(py_lib_project_config_python)" || return 1

  "$python_bin" - "$repo_root/pyproject.toml" <<'PY'
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

pyproject_path = Path(sys.argv[1])
with pyproject_path.open("rb") as pyproject_file:
    pyproject = tomllib.load(pyproject_file)

tooling = pyproject["tool"]["ternforge"]
env_prefix = tooling["env_prefix"].strip()

if not re.fullmatch(r"[A-Z][A-Z0-9_]*", env_prefix):
    msg = "[tool.ternforge].env_prefix must be an uppercase env-var prefix."
    raise SystemExit(msg)

print(env_prefix)
PY
}

py_lib_load_project_env_config() {
  local repo_root="${1:-$(pwd)}"
  local config_lines
  mapfile -t config_lines < <(py_lib_read_project_env_config "$repo_root") || return 1

  if [ "${#config_lines[@]}" -ne 1 ]; then
    return 1
  fi

  PY_LIB_PROJECT_ENV_PREFIX="${config_lines[0]}"

  export PY_LIB_PROJECT_ENV_PREFIX
}
