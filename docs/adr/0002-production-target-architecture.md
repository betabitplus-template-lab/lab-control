# ADR 0002: Production target architecture with commodity lifecycle tools

- Status: Proposed — conditional acceptance
- Date: 2026-07-15
- Scope: production design only; no production migration in this ADR
- Baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`

## Context

The legacy platform implements template assembly, manifests/builds, update wrappers, a downstream registry, fleet reporting/synchronization, repository onboarding and generic quality wrappers. The isolated first stage proved composed private Copier templates. The final stage asks which owned logic remains necessary when commodity tools are used directly.

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
15. Treat `py-lib-runtime` as an independent product library and normal Renovate dependency.
16. Do not build a new central fleet service. Renovate dashboards, GitHub PR/check state and OpenTofu plans are authoritative operational signals.

## Target topology

```text
components
  ↓ Renovate git-submodules PR
profile Copier template ── Release Please ── immutable tag
  ↓ Renovate Copier PR
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
- independent, reproducible versions and simple rollback;
- central CI changes without Copier file updates;
- repository configuration drift becomes a plan;
- least-privilege identities can be separated by function;
- owned code expresses only organization policy.

### Costs

- private consumers need read access to both template and components repositories;
- new output paths require explicit final-template wiring;
- workflow caller refs still need controlled updates;
- first repository bootstrap is inherently two-phase;
- private rulesets require a suitable GitHub plan;
- multiple commodity tools require disciplined version/SHA/digest pinning.

## Rejected alternatives

- manifest/build assembler;
- copied shared workflow bodies;
- Workflows write on the main Renovate identity by default;
- Backstage or a new platform service;
- mandatory custom fleet dashboard;
- Copier tasks executing routine lock refresh.

## Acceptance condition

This ADR becomes Accepted for production rollout only after private reusable workflow access, topic autodiscovery, OpenTofu no-drift, Release Please, lock refresh, tag protection and restricted-components credential tests pass in the isolated lab, and the private-ruleset capability decision is resolved.
