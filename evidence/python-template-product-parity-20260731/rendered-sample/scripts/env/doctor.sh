#!/usr/bin/env bash
set -euo pipefail

pass_count=0
warn_count=0
fail_count=0

pass() {
  printf '[PASS] %s\n' "$1"
  pass_count=$((pass_count + 1))
}

warn() {
  printf '[WARN] %s\n' "$1"
  warn_count=$((warn_count + 1))
}

fail() {
  printf '[FAIL] %s\n' "$1"
  fail_count=$((fail_count + 1))
}

require_command() {
  local command_name="$1"
  local hint="$2"

  if command -v "$command_name" >/dev/null 2>&1; then
    pass "Found \`$command_name\`"
    return 0
  fi

  fail "Missing \`$command_name\`. $hint"
  return 0
}

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

# shellcheck disable=SC1091
source "scripts/env/project_config.sh"

printf 'Sample Lib contributor doctor\n'
printf 'Repo: %s\n\n' "$repo_root"

require_command "git" "Install Git and rerun this check."
require_command "uv" "Install uv: https://docs.astral.sh/uv/getting-started/installation/"
require_command "direnv" "Install direnv and enable it in your shell."

if [ -x ".venv/bin/python" ]; then
  pass "Project virtualenv exists at \`.venv/\`"

  venv_python_version="$(
    .venv/bin/python - <<'PY'
import sys
print(".".join(map(str, sys.version_info[:3])))
raise SystemExit(0 if sys.version_info >= (3, 13) else 1)
PY
  )" || {
    fail "Repo virtualenv must use Python 3.13+. Current \`.venv\` interpreter: ${venv_python_version:-unknown}"
    venv_python_version=""
  }

  if [ -n "$venv_python_version" ]; then
    pass "Repo virtualenv uses Python ${venv_python_version}"
  fi
else
  fail "Project virtualenv is missing. Run \`bash scripts/env/setup.sh\`."

  if command -v python3 >/dev/null 2>&1; then
    system_python_version="$(
      python3 - <<'PY'
import sys
print(".".join(map(str, sys.version_info[:3])))
PY
    )"
    warn "System \`python3\` is ${system_python_version}. The repo still needs a local Python 3.13 environment."
  else
    fail "Missing \`python3\`. Install Python 3.13+ or let \`uv\` manage it during setup."
  fi
fi

if py_lib_load_project_env_config "$repo_root"; then
  pass "Read project env config from pyproject.toml"
else
  fail "Could not read [tool.ternforge] env config from pyproject.toml."
fi

pre_commit_hook="$(git rev-parse --git-path hooks/pre-commit)"
pre_push_hook="$(git rev-parse --git-path hooks/pre-push)"

if [ -f "$pre_commit_hook" ] && [ -f "$pre_push_hook" ]; then
  pass "Git hooks are installed"
else
  warn "Git hooks are missing. Run \`bash scripts/env/setup.sh\` to install them."
fi

if command -v gh >/dev/null 2>&1; then
  if gh auth status -h github.com >/dev/null 2>&1; then
    pass "GitHub CLI is installed and authenticated"
  else
    warn "GitHub CLI is installed but not authenticated. Run \`gh auth login\`."
  fi
else
  warn "GitHub CLI is not installed. Recommended for PR and CI workflows."
fi

printf '\nSummary: %s passed, %s warnings, %s failed\n' \
  "$pass_count" "$warn_count" "$fail_count"

if [ "$fail_count" -gt 0 ]; then
  printf '%s\n' "Suggested fixes: bash scripts/env/setup.sh, direnv allow, and optionally gh auth login."
  exit 1
fi
