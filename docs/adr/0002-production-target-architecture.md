# ADR 0002: Production target architecture with commodity lifecycle tools

- Status: Proposed — architecture validated; one functional rerun and rollout conditions remain
- Date: 2026-07-16
- Scope: production design only; no production migration in this ADR
- Baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`

## Context

The legacy platform implements template assembly, manifests/builds, update wrappers, a downstream registry, fleet reporting/synchronization, repository onboarding and generic quality wrappers. The isolated stages proved composed private Copier templates and tested which owned logic remains necessary when commodity tools are used directly.

## Decision

1. Keep shared source components in one private repository with no end-user versioning contract.
2. Mount components into each final Copier template as an exact committed submodule gitlink.
3. Keep final templates independent and release them independently.
4. Use Copier directly for generation and three-way updates.
5. Use Renovate for component gitlinks, Copier sources, package dependencies and GitHub Actions refs.
6. Replace registry membership with GitHub topics; derive template source/version from `.copier-answers.yml`.
7. Put reusable workflows and private Renovate presets in one automation repository.
8. Pin reusable workflows and Actions to exact commits; Renovate may detect changes but has no Workflows write.
9. Use a separate bounded workflow-publisher App/workflow for caller ref PRs.
10. Preserve `dev → main`; Renovate targets `dev`; an idempotent workflow creates but never merges a promotion PR.
11. Use OpenTofu GitHub provider for repositories, topics, merge settings, branches, default branch, variables, App access and rulesets where the GitHub plan exposes them.
12. Use Release Please for release PR, changelog, tag and GitHub Release; require template acceptance and verify exact main SHA.
13. Use direct quality/package tools without compatibility wrappers.
14. Keep only a small `py-lib-policy` checker for unique organization conventions.
15. Treat `py-lib-runtime` as product code and an ordinary Renovate dependency. While runtime and tooling share one root repository tag, detect them separately but group their ref update into one lock-safe PR.
16. Do not build a new central fleet service. Renovate dashboards, GitHub PR/check state and OpenTofu plans are authoritative operational signals.

## Target topology

```text
components
  ↓ Renovate git-submodules PR
profile Copier template ── Release Please ── immutable tag
  ↓ Renovate Copier PR + exact uv lock
managed downstream dev
  ↓ reusable CI / review
promotion PR
  ↓
main

OpenTofu → GitHub configuration
Renovate dashboards + GitHub checks + OpenTofu plan → fleet visibility
```

## Consequences

### Positive

- no custom template/update engine;
- no custom registry or fleet synchronizer in delivery;
- normal PR diffs and native Copier conflicts;
- independent, reproducible template versions and simple rollback;
- central CI changes without Copier file updates;
- repository configuration drift becomes a plan;
- least-privilege identities are separated by function;
- owned code expresses only organization policy or thin coordination.

### Costs

- private consumers need read access to both template and components repositories;
- new output paths require explicit final-template wiring;
- workflow caller refs still need controlled updates;
- first repository bootstrap is inherently two-phase;
- private rulesets require a suitable GitHub plan;
- multiple commodity tools require disciplined version/SHA/digest pinning;
- packages sharing one root Git tag must be updated as one ref group until separately released.

## Rejected alternatives

- manifest/build assembler;
- copied shared workflow bodies;
- Workflows write on the main Renovate identity by default;
- Backstage or a new platform service;
- mandatory custom fleet dashboard;
- Copier tasks executing routine lock refresh.

## Evidence state

Live positive evidence now covers private reusable workflows, private Renovate presets/topic discovery, Release Please through `v0.4.3`, private cross-platform template acceptance, OpenTofu creation and repeat-bootstrap idempotency, promotion PR idempotency, nested and legacy-answer lock updates, restricted components credentials, quality/policy parity and direct packaging.

Handoff-04 passed P04, T03 and K03. K06 failed because the regex replacement dropped the literal `v` and the grouping rule matched `packageName` instead of `depName`. Both defects are corrected in `lab-control#9` and reviewable `automation#1`; only the live grouped-PR rerun remains.

Private rulesets remain plan-blocked; the equivalent public resource shapes passed. Repository visibility is recorded as experimental state and is not itself an architecture acceptance condition.

## Acceptance condition

This ADR becomes Accepted for production rollout only after:

1. K06 creates one grouped runtime/tooling ref PR with a valid regenerated lock, green CI, no duplicate on rerun and automerge false;
2. current workflows pass final actionlint and `zizmor --pedantic --offline` revalidation;
3. the private P06/T04/L05 capability decision is resolved through a suitable plan or an explicitly approved lower-fidelity private fallback;
4. the incremental migration and rollback plan is reviewed before any production write.
