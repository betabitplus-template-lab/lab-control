#!/usr/bin/env bash
set -euo pipefail
root="${1:-template}"
test -d "$root"
broken="$(find -L "$root" -type l -print)"
test -z "$broken" || { printf 'Broken symlinks:\n%s\n' "$broken" >&2; exit 1; }
git diff --check
! git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- "$root"
while IFS= read -r path; do
  [[ -L "$path" ]] || continue
  target="$(realpath "$path")"
  case "$target" in "$PWD"/*) ;; *) echo "Symlink escapes checkout: $path -> $target" >&2; exit 1;; esac
done < <(git ls-files "$root")
