#!/usr/bin/env bash
# shellcheck shell=bash

py_lib_secret_env_files() {
  local repo_root="${1:-$PWD}"
  python3 - "$repo_root/pyproject.toml" <<'PY'
from __future__ import annotations

import sys
import tomllib
from pathlib import PurePosixPath

with open(sys.argv[1], "rb") as pyproject_file:
    pyproject = tomllib.load(pyproject_file)

secrets = (
    pyproject.get("tool", {})
    .get("ternforge", {})
    .get("secrets", {})
)
env_files = secrets.get("env_files")
if env_files is None:
    raise SystemExit
if not isinstance(env_files, list):
    raise SystemExit("[tool.ternforge.secrets].env_files must be a list.")

for env_file in env_files:
    if not isinstance(env_file, str) or not env_file.strip():
        raise SystemExit("Secret env file paths must be non-empty strings.")
    path = PurePosixPath(env_file.strip())
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
    if [ -n "$branch" ]; then
      git -C "$root" merge --ff-only --quiet "origin/$branch"
    fi
  elif [ -e "$root" ]; then
    printf '%s\n' "betabit-secrets cache path is not a Git checkout: $root" >&2
    return 1
  else
    mkdir -p "$(dirname "$root")"
    git clone --quiet "https://github.com/betabitplus/betabit-secrets.git" "$root"
  fi

  printf '%s\n' "$root"
}

py_lib_load_secrets() {
  local repo_root="${1:-$PWD}"
  local env_files secrets_root age_key_file env_file encrypted_env decrypted_env direnv_exports
  mapfile -t env_files < <(py_lib_secret_env_files "$repo_root") || return 1
  if [ "${#env_files[@]}" -eq 0 ]; then
    return 0
  fi

  command -v git >/dev/null 2>&1 || { printf '%s\n' "git is required." >&2; return 1; }
  command -v sops >/dev/null 2>&1 || { printf '%s\n' "sops is required." >&2; return 1; }
  command -v direnv >/dev/null 2>&1 || { printf '%s\n' "direnv is required." >&2; return 1; }

  secrets_root="$(py_lib_ensure_secrets_repo)" || return 1
  age_key_file="$HOME/.config/sops/age/keys.txt"
  for env_file in "${env_files[@]}"; do
    encrypted_env="$secrets_root/$env_file"
    if [ ! -f "$encrypted_env" ]; then
      printf '%s\n' "Encrypted env file not found: $env_file" >&2
      return 1
    fi
    if declare -F watch_file >/dev/null 2>&1; then
      watch_file "$encrypted_env"
    fi
    if [ -z "${SOPS_AGE_KEY_FILE:-}" ] && [ -f "$age_key_file" ]; then
      decrypted_env="$(SOPS_AGE_KEY_FILE="$age_key_file" sops decrypt "$encrypted_env")" || return 1
    else
      decrypted_env="$(sops decrypt "$encrypted_env")" || return 1
    fi
    direnv_exports="$(printf '%s\n' "$decrypted_env" | direnv dotenv bash /dev/stdin)" || return 1
    eval "$direnv_exports" || return 1
  done
}
