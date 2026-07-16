# ADR 0002: Production target architecture with commodity lifecycle tools

- Status: Accepted for target architecture — production rollout remains conditional
- Date: 2026-07-16
- Scope: production design only; no production migration in this ADR
- Baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`

## Context

The legacy platform implements template assembly, manifests/builds, update wrappers, a downstream registry, fleet reporting/synchronization, repository onboarding and generic quality wrappers. The isolated stages tested which owned logic remains necessary when commodity tools are used directly.

## Decision

1. Keep shared source components in one private repository with no end-user versioning contract.
2. Mount components into each final Copier template as an exact committed submodule gitlink.
3. Keep final templates independent and release them independently.
4. Use Copier directly for generation and three-way updates.
5. Use Renovate for component gitlinks, Copier sources, package dependencies and GitHub Actions refs.
6. Replace registry membership with GitHub topics; derive template source/version from `.copier-answers.yml`.
7. Put reusable workflows and private Renovate presets in one automation repository.
8. Pin reusable workflows and Actions to exact commits; ordinary Renovate has no Workflows write.
9. Use a separate bounded workflow-publisher App/workflow for caller ref PRs.
10. Preserve `dev → main`; Renovate targets `dev`; an idempotent workflow creates but never merges a promotion PR.
11. Use OpenTofu GitHub provider for repositories, topics, merge settings, branches, default branch, variables, App access and rulesets where the GitHub plan exposes them.
12. Use Release Please for release PR, changelog, tag and GitHub Release; require template acceptance and verify exact main SHA.
13. Use direct quality/package tools without compatibility wrappers.
14. Keep only a small `py-lib-policy` checker for unique organization conventions.
15. Treat `py-lib-runtime` as product code and an ordinary Renovate dependency. While runtime and tooling share one root repository tag, detect them separately but update their refs in one lock-safe group.
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
- credentials can remain separated by function;
- owned code expresses only organization policy or thin coordination.

### Costs

- private consumers need read access to template and components repositories;
- new output paths require explicit final-template wiring;
- workflow caller refs need the bounded publisher;
- first repository bootstrap is inherently two-phase;
- private rulesets require suitable GitHub plan capability or an approved fallback;
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

The isolated functional validation is complete.

Live positive evidence covers:

- private reusable workflows and exact-SHA callers;
- private Renovate presets and topic discovery;
- Release Please through `v0.4.3`;
- private Linux/macOS/Windows template acceptance;
- OpenTofu creation, state recovery and repeat-bootstrap idempotency;
- duplicate-free promotion PR creation;
- root, nested and legacy-answer lock updates;
- one grouped runtime/tooling PEP 508 Git update with regenerated lock and idempotent rerun;
- restricted components credential behavior;
- quality and residual-policy parity;
- direct wheel/sdist packaging and isolated installation;
- final actionlint and pedantic/offline zizmor checks with zero findings.

Final K06 evidence is `sandbox-process#11` at `23180206f1df692ca3d0627edc69c86aadd19454`, created from `automation#1@1554ac4295daa4c75d983ddab0fca1442b33e675`, with CI run `29487631571` successful and no duplicate on rerun.

Private rulesets remain plan-blocked; equivalent public configurations passed. Repository visibility is experimental state, not a missing code path.

## Rollout conditions

The target architecture is accepted. Production rollout remains conditional on:

1. resolving private P06/T04/L05 through suitable plan capability or an explicitly approved and tested lower-fidelity fallback;
2. reviewing incremental migration and rollback sequencing;
3. validating the chosen private protection model in one pilot repository before broad adoption;
4. preserving review gates, automerge-off defaults and immediate rollback throughout migration.

No production migration is authorized by this ADR.
