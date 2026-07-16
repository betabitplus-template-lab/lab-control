# Production-shaped template platform experiment: final result

Date: 2026-07-16  
Organization: `betabitplus-template-lab`  
Frozen/read-only production baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`  
Primary implementation: [lab-control#9](https://github.com/betabitplus-template-lab/lab-control/pull/9)

```text
Architecture decision:
    CONDITIONAL GO

Experiment acceptance:
    INCOMPLETE — one corrected live K06 check remains

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

The architectural conclusion is stable. Copier, Renovate, GitHub Actions/Apps, OpenTofu, Release Please, uv and direct community quality/package tools replace the custom template assembler/update engine, registry, fleet synchronizer, onboarding API subsystem, release controller and most wrappers. No replacement platform service or lifecycle package is required.

Handoff-04 closed P04, T03 and K03. K06 remains the only unaccepted functional item. Its failure is deterministic Renovate preset behavior, not permissions, credentials, repository visibility or the GitHub plan. The two defects are fixed and published in review; one live Renovate rerun is required before the experiment can be declared functionally complete.

The decision remains **CONDITIONAL GO** because private rulesets are unavailable on the current GitHub plan. Equivalent public ruleset shapes passed, so the report records private and public capability separately rather than treating the tariff limitation as an implementation failure.

No production migration has started. Every production audit reports zero mutations.

## Handoff-04 scorecard

Bundle SHA-256: `ffa83d8f2d252d5a42be4dda64d3185b30dd253c83a84683096b3eb59bbdc136`.

| ID | Status | Result |
|---|---|---|
| P04 | PASS | promotion controller succeeded twice against one `dev → main` PR, with no duplicate and no automerge |
| T03 | PASS | repeat bootstrap exited 0 without mutation; subsequent OpenTofu plan was clean |
| K03 | PASS | `python-lib@v0.4.3` produced a legacy-answer Copier PR containing generated changes and a real `uv.lock` update; CI passed |
| K06 | FAIL | live replacement dropped the literal `v` and runtime/tooling were assigned separate branches instead of one group |

The immutable summary is [`handoff-04-summary.json`](../evidence/handoff-04-summary.json); the evidence interpretation is [`handoff-04-integration-results.md`](handoff-04-integration-results.md).

## Accepted final live evidence

### P04 — promotion controller

- automation commit: `9b90c1df2d69ed3c8c2fa27e11f78e2b940a386a`;
- caller commit: `a41a511c9656faed0bfa053ead2d67e381f3a5b3`;
- promotion PR: `sandbox-process#2`, `dev → main`, open, automerge false;
- workflow run `29422268451`, attempts 1 and 2 both successful;
- compare result remained `ahead_by=7`;
- second run created no duplicate PR.

### T03 — bootstrap idempotency

- repository: `sandbox-provisioned`;
- remote `dev` already existed;
- repeat bootstrap exit: `0`;
- `dev` and `main` remained at `2a79e75a46131b496a621384c7b62441734f245c`;
- no new commit, branch or rejected push;
- OpenTofu plan exit: `0`, no unexplained changes.

### K03 — legacy answers and real lock change

- `components#5` merged the remediation component;
- `python-lib#21` published the rendered component change;
- release PR `python-lib#22` produced immutable tag `v0.4.3` at `5df5992c7af0bf4393b712525573699c36cd6c9b`;
- GitHub release ID: `354495776`;
- downstream PR: `sandbox-process#10`, open, mergeable, automerge false;
- changed files: `.copier-answers.yml`, `.pre-commit-config.yaml`, `pyproject.toml`, `uv.lock`;
- obsolete `py-lib-template-check` hook absent;
- `uv lock --check` passed;
- CI run `29424887496` passed on Linux and macOS;
- rerunning Renovate changed neither the head nor PR count.

The K06 run inadvertently pruned some stale Renovate branches. The agent restored the recorded refs, reopened PRs `#4`, `#5` and `#10`, rebuilt `#10` from current `dev`, and reran its CI successfully. The mutation and cleanup audit records the entire sequence.

## K06 failure and correction

Handoff-04 proved extraction and lookup for both dependencies:

```text
py-lib-runtime @ ...py-lib-starter.git@v0.32.3#subdirectory=packages/py-lib-runtime
py-lib-tooling @ ...py-lib-starter.git@v0.32.3#subdirectory=packages/py-lib-tooling
```

Both resolved through package `betabitplus/py-lib-starter`, datasource `github-tags`, with update `v0.32.3 → v0.32.4`. The live update failed for two configuration reasons:

1. `currentValue` included `v`, while `extractVersionTemplate` normalized the new version to digits. Renovate therefore wrote `@0.32.4`, and the literal `@v...` manager could not re-extract the updated file.
2. The package rule matched dependency aliases through `matchPackageNames`, but both records have the shared source package name `betabitplus/py-lib-starter`. Their distinct aliases are `depName` values.

The correction now:

- keeps literal `v` outside the captured `currentValue`;
- matches the group with `matchDepNames`;
- requires `minimumGroupSize: 2`, preventing a partial shared-source update;
- includes a Node regression test for extraction, replacement, re-extraction and grouping.

Reviewable implementation:

- `lab-control#9` commits `88e756cdead0ffb751c55af50483b6fd48faaf9f` and `0dbdc7448f201e129670768b4e6d5b2d231e23a2`;
- `automation#1`, exact commit `1554ac4295daa4c75d983ddab0fca1442b33e675`, draft, automerge disabled.

Only a K06 live rerun remains. No other acceptance phase needs repeating.

## Private and public capability

Current lab visibility is public and was not changed in handoff-04.

| Capability | Private repositories | Public repositories |
|---|---|---|
| ordinary Git, Copier, reusable workflow, Renovate and release flows | PASS | PASS |
| branch/tag rulesets on the current plan | BLOCKED — HTTP 403 | PASS |

This is a tariff/capability boundary, not an architecture defect. Production rollout must either obtain private-ruleset capability or explicitly accept and test a lower-fidelity private branch-protection alternative.

## Security and safety

Handoff-04 results:

- actionlint 1.7.12: exit `0`;
- `bash -n provisioning/bootstrap.sh`: exit `0`;
- zizmor 1.27.0 pedantic/offline: one low finding, zero medium/high;
- production mutations: `0`;
- visibility mutations: `0`;
- automerge enables: `0`;
- credentials created or rotated: `0`;
- credential/private-key/header/credential-URL scan findings: `0`;
- `sandbox-python-lib#3`: open, unmerged and unchanged.

The single zizmor finding requested an explanatory comment for the necessary `pull-requests: write` permission. The comment was already present immediately above it; it is now inline in commit `415487ffeb5beba6b0c622f96033421328a32c75` so the audit can associate it with the permission. A final static rerun accompanies K06.

## Replacement inventory and retained surface

The matrix still covers all 25 commands and 127 production modules.

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

`py-lib-runtime` remains a 2,133-LOC product library and is excluded from the lifecycle denominator.

## Final decision rule

After one successful K06 rerun, the isolated experiment is functionally complete. The architecture decision will still be **CONDITIONAL GO** until the private-ruleset capability decision is resolved.

PR #9 remains draft until the K06 live evidence and final static rerun are incorporated. No production migration has started.
