# Production-shaped template platform experiment: final result

Date: 2026-07-15  
Organization: `betabitplus-template-lab`  
Frozen/read-only production baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`  
Primary implementation: [lab-control#9](https://github.com/betabitplus-template-lab/lab-control/pull/9)

```text
Architecture decision:
    CONDITIONAL GO

Experiment acceptance:
    INCOMPLETE — four corrected live items require final revalidation

Production repositories changed:
    0

Current root + tooling custom source:
    11,466 LOC

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

The principal architectural result is positive. Copier, Renovate, GitHub Actions and Apps, OpenTofu, Release Please, uv and direct community quality/package tools can replace the custom template assembler/update engine, registry, fleet synchronizer, onboarding API subsystem, release controller and most wrappers.

The decision remains **CONDITIONAL GO** because:

1. private branch/tag rulesets are unavailable on the current GitHub plan;
2. handoff-03 passed eight corrected items but left P04, T03, K03 and K06 as live failures;
3. workflow hardening added after handoff-03 requires one final actionlint/zizmor run.

Repository visibility is no longer a final functional prerequisite. The evidence is recorded separately:

- private execution passed all tested private flows except plan-blocked private rulesets;
- public execution proved that the same ruleset configurations work where GitHub exposes them.

No production migration has started and every production audit reports zero mutations.

## Evidence scorecards

### Handoff-02

Bundle SHA-256: `5894d7468d2a5473e44c649fccebbff139c79f391b044014992de495b1ef18d6`.

| Status | Count |
|---|---:|
| PASS | 40 |
| NEGATIVE_PASS | 6 |
| FAIL | 10 |
| BLOCKED | 5 |

### Handoff-03

Bundle SHA-256: `4e541e17fc23872bc9203576debbb63f017d53b7a259eeb9955fd72fae98fb47`.

| Status | Count |
|---|---:|
| PASS | 8 |
| NEGATIVE_PASS | 0 |
| FAIL | 4 |
| BLOCKED among the 12 revalidated IDs | 0 |

Passed IDs: `S03 S04 R03 T01 L04 K05 D03 D05`.  
Failed IDs: `P04 T03 K03 K06`.  
Unchanged private blockers: `P06 T04 L05`.

Safety remained intact:

- production mutations: `0`;
- automerge: disabled across 53 inspected PRs;
- `sandbox-python-lib#3`: open, unmerged and unchanged;
- private key/credential/state findings: `0`;
- historical tags/releases: not rewritten.

## Accepted live architecture evidence

### Private reusable workflows

Private cross-repository calls passed with exact source SHAs, read-only caller permissions, inherited secrets without disclosure, Linux/macOS lanes, intentional failure propagation and cancellation propagation.

### Renovate discovery and delivery

Private presets, explicit allowlist extract/lookup/full phases, organization/topic discovery, reviewed live PR creation and idempotent reruns passed with automerge disabled. Topics plus repository-local Copier relationships can replace the custom downstream registry.

### Repository process

`sandbox-process` was created with `dev` as default and a `main` promotion baseline. A safe update reached `dev` through reviewed CI and exactly one `dev → main` PR remained. The remaining P04 failure is confined to missing repository context on a no-checkout GitHub CLI command; the current workflow now scopes every PR command explicitly.

### Declarative provisioning

OpenTofu 1.12.0 with GitHub provider 6.6.0 created `sandbox-provisioned` without manual repository creation, applied the repository-only phase, reconciled/imported state and cleaned up. T03 remains pending only because the original repeat bootstrap authored another local commit. The corrected script checks remote `dev` before rendering and exits successfully when initialized.

### Releases

Release Please produced immutable patch releases without moving historical tags:

| Release | Main/tag target | Release ID |
|---|---|---:|
| `python-lib@v0.4.0` | `0477653722f8a8b125e2bd3963b37d4a0d10c153` | `354133543` |
| `python-lib@v0.4.1` | `1a4fabe2c0449c5fe92d745eea0f9494c6fed160` | `354137656` |
| `python-lib@v0.4.2` | `2940bc355da2a957e0deb6c1660ce57293e9674b` | `354387791` |

The v0.4.2 private acceptance path passed on Linux, macOS and Windows.

### Locks, nested relationships and ordinary dependencies

- root lock baseline and CI passed;
- both nested workspace locks regenerated idempotently;
- nested acceptance checks equal valid semver tags rather than a historical constant;
- PEP 508 runtime/tooling refs are detected separately;
- because both packages currently publish from one root tag, their update is grouped into one PR;
- the legacy-answer case still needs one component/template release that removes the obsolete hook and forces a deterministic lock change.

### Quality, packaging and residual policy

Direct rule parity passed 8/8; residual policy parity passed 12/12. The corrected dependency-free policy checker accepted the exact generated baseline. Wheel/sdist build, metadata validation, isolated installs, public import, console smoke and pytest passed.

Artifact SHA-256:

- wheel: `d0a4f11f563aeded804fd86ecf82e576f3d1589b454b62055a55223c35553041`;
- sdist: `b88e32fd2068ec8aab65fe9f07a21cc4bfb2c00aeb00ac160369a3ab01933fcc`.

## Remaining functional gate

| ID | Handoff-03 result | Correction in current PR branch |
|---|---|---|
| P04 | workflow lacked repository context outside a checkout | repository-scoped compare/list/create commands |
| T03 | repeat bootstrap authored a second local commit | remote `dev` guard before render/commit |
| K03 | no `uv.lock`; inherited hook called obsolete legacy checker | component patch removes hook and forces deterministic dependency metadata change |
| K06 | Renovate dependency-name mismatch and mixed source refs | two literal managers and one grouped shared-root-tag PR |

Exact live instructions: [`local-agent-handoff-04.md`](local-agent-handoff-04.md).

## Private rulesets and public fallback

Private P06/T04/L05 return a plan-related HTTP 403. Handoff-03 also demonstrated that the equivalent branch/tag policies work when repositories are public.

The final capability statement is therefore:

| Capability | Private repository | Public repository |
|---|---|---|
| ordinary Git, Copier, reusable workflows, Renovate and releases | PASS | PASS |
| branch/tag rulesets on the current plan | BLOCKED | PASS |

No visibility change is required for the remaining P04/T03/K03/K06 checks. The current visibility must simply be recorded accurately.

## Security hardening after handoff-03

The experiment branch now:

- pins action uses to exact commit SHAs;
- restricts App tokens to explicit lab repository lists;
- requests explicit App permissions;
- uses `persist-credentials:false`;
- uses temporary askpass only around required pushes;
- adds workflow concurrency and job names;
- keeps the Renovate container digest-pinned;
- moves promotion PR write permission to the single job that needs it.

The current branch requires a fresh actionlint and `zizmor --pedantic --offline` run. No whole-repository security pass is claimed before that evidence returns.

## Replacement inventory and retained surface

The matrices cover all 25 published commands and 127 production modules.

| Classification | Commands | Modules |
|---|---:|---:|
| DELETE | 8 | 44 |
| REPLACE | 14 | 40 |
| RETAIN_MINIMAL | 2 → one checker | 6 |
| PRODUCT_LIBRARY | 0 | 26 |
| DEFER | 1 | 11 |

`py-lib-runtime` remains a 2,133-LOC product library, outside the platform lifecycle denominator.

Retained executable surface:

- idempotent Copier bootstrap: 25 LOC;
- promotion PR workflow: 26 LOC;
- Renovate phase guard: 11 LOC;
- optional trusted workflow-ref updater: 103 LOC;
- generic wiring guard: 12 LOC;
- unique policy checker: 196 LOC.

Preferred lifecycle total: **165 LOC**, a **97.5% reduction** from 6,673 strict lifecycle LOC.  
Total executable non-product surface: **373 LOC**, a **96.7% reduction** from 11,466 root/tooling LOC.

## Rollout prerequisites

1. Complete P04/T03/K03/K06 handoff-04 revalidation.
2. Record private rulesets as plan-blocked and public rulesets as passed; choose a production plan or an explicitly approved private fallback before migration.
3. Require a zero-exit actionlint/zizmor result for the current workflow set.
4. Review migration and rollback repository by repository.
5. Start with one production pilot; do not mass-switch production.

## Final decision rule

The architecture meets the principal goal: no custom platform package is required for template assembly/update, registry membership, fleet synchronization, repository APIs, routine dependency freshness, reusable CI distribution, releases or generic quality tooling.

The final decision remains **CONDITIONAL GO** until the four bounded live checks pass and the external private-ruleset decision is resolved. PR #9 remains draft. No production migration has started.