#!/usr/bin/env bash
set -euo pipefail
: "${REPOSITORY:?owner/name required}"
: "${TEMPLATE_URL:?private Copier template URL required}"
: "${TEMPLATE_REF:?immutable template tag required}"
workdir="${WORKDIR:-$(mktemp -d)}"
project="$workdir/project"

case "$REPOSITORY" in betabitplus-template-lab/*) ;; *) echo 'lab repositories only' >&2; exit 2;; esac
copier copy --trust --vcs-ref "$TEMPLATE_REF" --defaults "$TEMPLATE_URL" "$project"
cd "$project"
git init
git checkout -b dev
git add --all
git -c user.name='lab bootstrap' -c user.email='noreply@example.invalid' commit -m 'chore: bootstrap managed repository'
git remote add origin "https://github.com/${REPOSITORY}.git"
git push --set-upstream origin dev
# main is created declaratively by the second OpenTofu phase from this exact dev baseline.
