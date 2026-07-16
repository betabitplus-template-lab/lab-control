#!/usr/bin/env bash
set -euo pipefail
: "${REPOSITORY:?owner/name required}"
: "${TEMPLATE_URL:?private Copier template URL required}"
: "${TEMPLATE_REF:?immutable template tag required}"
workdir="${WORKDIR:-$(mktemp -d)}"
project="$workdir/project"
remote="https://github.com/${REPOSITORY}.git"

case "$REPOSITORY" in betabitplus-template-lab/*) ;; *) echo 'lab repositories only' >&2; exit 2;; esac
set +e
git ls-remote --exit-code "$remote" refs/heads/dev >"$workdir/dev-ref.txt" 2>"$workdir/dev-ref.err"
status=$?
set -e
case "$status" in
  0) echo 'dev already exists; bootstrap is complete'; exit 0 ;;
  2) ;;
  *) cat "$workdir/dev-ref.err" >&2; exit "$status" ;;
esac
copier copy --trust --vcs-ref "$TEMPLATE_REF" --defaults "$TEMPLATE_URL" "$project"
cd "$project"
git init
git checkout -b dev
git add --all
git -c user.name='lab bootstrap' -c user.email='noreply@example.invalid' commit -m 'chore: bootstrap managed repository'
git remote add origin "$remote"
git push --set-upstream origin dev
# main is created declaratively by the second OpenTofu phase from this exact dev baseline.
