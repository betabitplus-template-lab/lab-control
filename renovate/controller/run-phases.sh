#!/usr/bin/env bash
set -euo pipefail
: "${RENOVATE_TOKEN:?lab-only Renovate installation token is required}"
: "${RENOVATE_IMAGE:?immutable Renovate image reference with sha256 digest is required}"
case "$RENOVATE_IMAGE" in *@sha256:*) ;; *) echo 'RENOVATE_IMAGE must be digest-pinned' >&2; exit 2;; esac
for phase in extract lookup full; do
  docker run --rm \
    -e RENOVATE_TOKEN \
    -e RENOVATE_DRY_RUN="$phase" \
    -v "$PWD/renovate/controller/config.js:/usr/src/app/config.js:ro" \
    "$RENOVATE_IMAGE" renovate
done
