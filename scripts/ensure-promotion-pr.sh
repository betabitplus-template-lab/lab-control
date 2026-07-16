#!/usr/bin/env bash
set -euo pipefail
: "${GH_TOKEN:?token required}"
: "${GITHUB_REPOSITORY:?owner/name required}"
case "$GITHUB_REPOSITORY" in betabitplus-template-lab/*) ;; *) echo 'lab repositories only' >&2; exit 2;; esac
if git diff --quiet origin/main...origin/dev; then
  echo 'No dev → main diff.'
  exit 0
fi
existing="$(gh pr list --repo "$GITHUB_REPOSITORY" --base main --head dev --state open --json number --jq '.[0].number // empty')"
if [[ -n "$existing" ]]; then
  echo "Promotion PR #$existing already exists."
  exit 0
fi
gh pr create --repo "$GITHUB_REPOSITORY" --base main --head dev \
  --title 'chore: promote dev to main' \
  --body 'Automated idempotent promotion proposal. This workflow never merges the PR.'
