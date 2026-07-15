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

The principal architectural result remains positive. Copier, Renovate, GitHub Actions and Apps, OpenTofu, Release Please, uv and direct community quality/package tools can replace the custom template assembler/update engine, registry, fleet synchronizer, onboarding API subsystem, release controller and most wrappers.

The correct decision is **CONDITIONAL GO**, not unconditional rollout:

1. private branch/tag rulesets remain unavailable on the current GitHub plan;
2. handoff-03 passed eight corrected items but left P04, T03, K03 and K06 as live failures;
3. the handoff-03 agent changed all eleven lab repositories to public outside the bounded instruction, so the private lab shape must be restored;
4. workflow hardening added after the handoff requires one final actionlint/zizmor run.

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

The immutable interpretation is [`handoff-02-integration-results.md`](handoff-02-integration-results.md).

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

The source status is preserved in [`handoff-03-summary.json`](../evidence/handoff-03-summary.json); interpretation is in [`handoff-03-integration-results.md`](handoff-03-integration-results.md).

Safety remained intact:

- production mutations: `0`;
- automerge: disabled across 53 inspected PRs;
- `sandbox-python-lib#3`: open, unmerged and unchanged;
- private key/credential/state findings: `0`;
- historical tags/releases: not rewritten.

## Live architecture proof

### Private reusable workflows

Private cross-repository workflow calls passed with exact source SHAs, read-only caller permissions, inherited secrets without disclosure, Linux/macOS lanes, intentional failure propagation and cancellation propagation. Thin callers can therefore replace copied CI bodies.

### Renovate discovery and delivery

Private presets, explicit allowlist extract/lookup/full phases, organization/topic discovery, reviewed live PR creation and idempotent reruns passed with automerge disabled. Topics plus repository-local Copier relationships can replace the custom downstream registry.

### Repository process

`sandbox-process` was created with `dev` as default and a `main` promotion baseline. A safe update reached `dev` through reviewed CI and exactly one `dev → main` PR remained. The remaining P04 failure is confined to missing `--repo` on a no-checkout GitHub CLI command; the current workflow now scopes every PR command explicitly.

### Declarative provisioning

OpenTofu 1.12.0 with GitHub provider 6.6.0 created `sandbox-provisioned` without manual repository creation, applied the repository-only phase, reconciled/imported state and cleaned up. T03 remains pending only because the original repeat bootstrap rendered and committed again before a rejected push. The corrected script checks remote `dev` before rendering and exits 0 when initialized.

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
- the nested acceptance fixture now checks equal valid semver tags rather than historical `v0.2.0`;
- PEP 508 runtime/tooling refs are detected by two literal Renovate managers;
- because both packages currently publish from one root tag, their ref update is grouped into one PR while remaining separately extracted;
- the final legacy-answer test still needs one generated component release that removes the obsolete legacy hook and forces a deterministic lock metadata change.

### Quality, packaging and residual policy

Direct rule parity passed 8/8; residual policy parity passed 12/12. The corrected dependency-free policy checker accepted the exact real generated baseline. Wheel/sdist build, metadata validation, isolated installs, public import, console smoke and pytest passed.

Artifact SHA-256:

- wheel: `d0a4f11f563aeded804fd86ecf82e576f3d1589b454b62055a55223c35553041`;
- sdist: `b88e32fd2068ec8aab65fe9f07a21cc4bfb2c00aeb00ac160369a3ab01933fcc`.

## Remaining functional gate

| ID | Handoff-03 result | Correction in PR #9 |
|---|---|---|
| P04 | workflow failed outside a checkout because `gh pr list` lacked `--repo` | repository-scoped compare/list/create; commit `80a0a70b2f2ab1fe78b26f8ebcdc8c09a6c5d382` |
| T03 | repeat bootstrap authored a second local commit | remote `dev` guard before render/commit; commit `74413a8c31dc9315e7c8f0859af0898f43ff91fc` |
| K03 | no `uv.lock`; inherited hook expected `_copier_answers.yml` | exact component patch at commit `ec9b692bccf4856e3a8049d9368a3613af942789` |
| K06 | Renovate `depName mismatch` and mixed source refs | literal managers and one grouped shared-root-tag PR; commit `6d792bfa88df3b2bd6b973f428427a6db2fe450c` |

Exact live instructions: [`local-agent-handoff-04.md`](local-agent-handoff-04.md).

## Private rulesets and public fallback

Private P06/T04/L05 continue to return the GitHub plan-related HTTP 403. Handoff-03 also demonstrated that branch/tag policies work when the lab repositories are public. That evidence is supplementary only and does not satisfy the private target.

The agent changed all eleven lab repositories to public. Handoff-04 must preserve the fallback evidence, remove only the recorded fallback controls and restore every lab repository to private before any other functional work.

## Security hardening after handoff-03

The handoff's whole-repository pedantic zizmor run found inherited first-stage workflow issues. The experiment branch now:

- pins action uses to exact commit SHAs;
- restricts App tokens to explicit lab repository lists;
- requests explicit App permissions;
- uses `persist-credentials:false`;
- uses temporary askpass only around required pushes;
- adds workflow concurrency and job names;
- keeps the Renovate container digest-pinned;
- moves promotion PR write permission to the single job that needs it.

The current branch still requires a fresh actionlint and `zizmor --pedantic --offline` run. No whole-repository security pass is claimed before that evidence returns.

## Replacement inventory

The authoritative matrices cover all 25 published commands and 127 production modules.

| Classification | Commands | Modules |
|---|---:|---:|
| DELETE | 8 | 44 |
| REPLACE | 14 | 40 |
| RETAIN_MINIMAL | 2 → one checker | 6 |
| PRODUCT_LIBRARY | 0 | 26 |
| DEFER | 1 | 11 |

`py-lib-runtime` remains a 2,133-LOC product library, outside the platform lifecycle denominator.

## Minimal retained surface

- idempotent Copier bootstrap: 25 LOC;
- promotion PR workflow: 26 LOC;
- Renovate phase guard: 11 LOC;
- optional trusted workflow-ref updater: 103 LOC;
- generic wiring guard: 12 LOC;
- unique policy checker: 196 LOC.

Preferred lifecycle total: **165 LOC**, a **97.5% reduction** from 6,673 strict lifecycle LOC.  
Total executable non-product surface: **373 LOC**, a **96.7% reduction** from 11,466 root/tooling LOC.

## Rollout prerequisites

1. Restore all lab repositories to private.
2. Complete P04/T03/K03/K06 handoff-04 revalidation.
3. Obtain private ruleset capability or approve and separately test a lower-fidelity private branch-protection fallback.
4. Require a zero-exit actionlint/zizmor result for the current workflow set.
5. Review migration/rollback repository by repository.
6. Start with one non-production-shaped pilot; do not mass-switch production.

## Final decision rule

The architecture meets the principal goal: no custom platform package is required for template assembly/update, registry membership, fleet synchronization, repository APIs, routine dependency freshness, reusable CI distribution, releases or generic quality tooling.

The final decision remains **CONDITIONAL GO** until the four bounded live checks pass, the lab is private again, and the external private-ruleset decision is resolved. PR #9 must remain draft. No production migration has started.
