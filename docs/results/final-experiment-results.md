# Production-shaped template platform experiment: final result

Date: 2026-07-16  
Organization: `betabitplus-template-lab`  
Frozen/read-only production baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`  
Primary implementation: [lab-control#9](https://github.com/betabitplus-template-lab/lab-control/pull/9)

```text
Architecture decision:
    CONDITIONAL GO

Isolated experiment acceptance:
    FUNCTIONALLY COMPLETE

Unresolved functional acceptance IDs:
    0

Production repositories changed:
    0

Current strict template/update lifecycle:
    6,673 LOC

Projected required custom lifecycle:
    165 LOC

Projected executable non-product custom surface:
    373 LOC

Published commands:
    8 delete
    14 replace
    2 collapse into one policy checker
    1 optional developer utility deferred
```

## Executive conclusion

The isolated experiment is functionally complete. Copier, Renovate, GitHub Actions/Apps, OpenTofu, Release Please, uv and direct community quality/package tools can replace the custom template assembler/update engine, downstream registry, fleet synchronizer, onboarding API subsystem, release controller and most generic wrappers. No replacement central platform service or custom lifecycle package is required.

All bounded functional acceptance items now pass. Handoff-04 closed P04, T03 and K03; the final K06 rerun closed the grouped PEP 508 Git dependency path and the final workflow-security rerun.

The architecture decision remains **CONDITIONAL GO**, rather than unconditional production rollout, because private branch/tag rulesets are unavailable on the current GitHub plan. Equivalent public ruleset configurations passed. This is now an explicit product-plan/operating-policy decision, not an untested implementation defect.

No production migration has started. Every audit reports zero production mutations.

## Final scorecards

### Handoff-04

Bundle SHA-256: `ffa83d8f2d252d5a42be4dda64d3185b30dd253c83a84683096b3eb59bbdc136`.

| ID | Status | Result |
|---|---|---|
| P04 | PASS | promotion controller succeeded twice against one `dev → main` PR, with no duplicate and no automerge |
| T03 | PASS | repeat bootstrap exited 0 without mutation; subsequent OpenTofu plan was clean |
| K03 | PASS | `python-lib@v0.4.3` produced a legacy-answer Copier PR with generated changes and a real `uv.lock` update; CI passed |
| K06 | FAIL in this historical run | exposed two final Renovate preset defects later corrected and passed in the bounded final rerun |

Historical interpretation: [`handoff-04-integration-results.md`](handoff-04-integration-results.md).

### K06 final rerun

Archive SHA-256: `7a32d84eb1e11468bd9d4de49be6857e509c47d1a99e8f7e1e26e9f7e63ad811`.

| ID | Status | Result |
|---|---|---|
| K06 | PASS | one grouped runtime/tooling update PR, valid `@v...` replacement, regenerated lock, green CI, duplicate-free rerun |

Machine-readable summary: [`k06-final-summary.json`](../evidence/k06-final-summary.json).  
Authoritative interpretation: [`k06-final-integration-results.md`](k06-final-integration-results.md).

## Accepted final live evidence

### P04 — promotion controller

- automation commit: `9b90c1df2d69ed3c8c2fa27e11f78e2b940a386a`;
- caller commit: `a41a511c9656faed0bfa053ead2d67e381f3a5b3`;
- promotion PR: `sandbox-process#2`, `dev → main`, open, automerge false;
- workflow run `29422268451`, attempts 1 and 2 successful;
- compare result remained `ahead_by=7`;
- second run created no duplicate PR.

### T03 — bootstrap idempotency

- repository: `sandbox-provisioned`;
- repeat bootstrap exit: `0`;
- `dev` and `main` remained at `2a79e75a46131b496a621384c7b62441734f245c`;
- no new commit, branch or rejected push;
- subsequent OpenTofu plan exit: `0`, with no unexplained changes.

### K03 — legacy answers and real lock change

- `components#5` merged the component remediation;
- `python-lib#21` published the rendered template change;
- release PR `python-lib#22` produced immutable tag `v0.4.3` at `5df5992c7af0bf4393b712525573699c36cd6c9b`;
- GitHub release ID: `354495776`;
- downstream PR: `sandbox-process#10`, open, mergeable, automerge false;
- changed files: `.copier-answers.yml`, `.pre-commit-config.yaml`, `pyproject.toml`, `uv.lock`;
- obsolete `py-lib-template-check` hook absent;
- `uv lock --check` passed;
- CI run `29424887496` passed on Linux and macOS;
- Renovate rerun changed neither the head nor PR count.

### K06 — grouped PEP 508 Git dependencies

Validated preset:

- repository: `betabitplus-template-lab/automation`;
- PR: `automation#1`;
- exact commit: `1554ac4295daa4c75d983ddab0fca1442b33e675`.

Validated consumer:

- repository: `betabitplus-template-lab/sandbox-process`;
- fixture base: `1a512157bcf29e205812c416d84a653f52aa9254`;
- grouped PR: `sandbox-process#11`;
- branch: `renovate-lab/shared-python-git-packages`;
- head: `23180206f1df692ca3d0627edc69c86aadd19454`;
- state: open and mergeable;
- automerge: false.

The PR atomically updates:

```text
py-lib-runtime: v0.32.3 -> v0.32.4
py-lib-tooling: v0.32.3 -> v0.32.4
```

The corrected preset preserves literal `@vX.Y.Z`, matches aliases through `matchDepNames`, requires `minimumGroupSize: 2`, and runs exact `uv lock` after the grouped update.

Accepted results:

- exactly one grouped PR and branch;
- changed files exactly `pyproject.toml` and `uv.lock`;
- updated-branch Renovate re-extraction found both dependencies at `0.32.4` with zero errors;
- `uv lock --check` exit `0`;
- CI run `29487631571` passed;
- jobs `87585796258` and `87585796277` passed;
- second Renovate run exit `0`;
- grouped branch head unchanged;
- duplicate PRs `0`;
- unrelated Renovate PRs and branches unchanged;
- `pruneStaleBranches=false` enforced.

## Private and public capability

Current lab visibility is public. The final experiment did not require another visibility change.

| Capability | Private repositories | Public repositories |
|---|---|---|
| ordinary Git, Copier, reusable workflow, Renovate and release flows | PASS | PASS |
| branch/tag rulesets on the current plan | BLOCKED — HTTP 403 | PASS |

This capability split is the only material external rollout blocker demonstrated by the lab. A private production pilot requires either suitable GitHub plan capability or an explicitly approved and separately tested lower-fidelity private branch-protection fallback.

## Security and safety

Final static results:

- downstream Renovate preset regression test: exit `0`;
- actionlint 1.7.12: exit `0`;
- `zizmor 1.27.0 --pedantic --offline .`: exit `0`, findings `0`.

Final safety results:

- production mutations: `0`;
- production repository/dev/tag snapshots: unchanged;
- visibility mutations in the final rerun: `0`;
- automerge enables: `0`;
- credentials/Apps/PATs/SSH keys/deploy keys created or rotated: `0`;
- credential/private-key/header/credential-URL findings: `0`;
- `sandbox-python-lib#3`: open, unmerged and unchanged at `82542cf617b2d55b2b609f5f53654e16e44f36bb`;
- historical tags, releases, C1/C2/C3 and prior evidence were not rewritten.

The agent temporarily disabled `enforce_admins` only on the lab-only `sandbox-process/dev` branch to publish the controlled fixture commit, then restored it to `true`; other protection settings were unchanged.

## Replacement inventory and retained surface

The matrix covers all 25 published commands and 127 production modules.

| Classification | Commands | Modules |
|---|---:|---:|
| DELETE | 8 | 44 |
| REPLACE | 14 | 40 |
| RETAIN_MINIMAL | 2 → one checker | 6 |
| PRODUCT_LIBRARY | 0 | 26 |
| DEFER | 1 | 11 |

Retained executable non-product surface:

- idempotent Copier bootstrap: 25 LOC;
- promotion PR workflow: 26 LOC;
- Renovate phase guard: 11 LOC;
- optional trusted workflow-ref updater: 103 LOC;
- generic wiring guard: 12 LOC;
- unique policy checker: 196 LOC.

Preferred lifecycle total: **165 LOC**, a **97.5% reduction** from 6,673 strict lifecycle LOC.  
Total executable non-product surface: **373 LOC**, a **96.7% reduction** from 11,466 root/tooling LOC.

`py-lib-runtime` remains a 2,133-LOC product library outside the lifecycle denominator.

## Final decision

The isolated technical experiment is complete and no additional local-agent handoff is required.

Production rollout remains conditional on:

1. choosing private-ruleset capability or approving/testing a lower-fidelity private fallback;
2. reviewing the incremental migration and rollback plan repository by repository;
3. starting with one non-production-shaped/private pilot before any broad migration.

PR #9 remains draft because it is an experiment and architecture package, not an authorized production migration. No production write has occurred.
