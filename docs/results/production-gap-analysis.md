# Production gap analysis

## Baselines

- Frozen comparison baseline: `d59582375855cff69fb165e467dc5847bc75ca99`.
- Production `dev` and tag snapshots remained unchanged in every audit.
- Production mutations during all experiment stages: **0**.

## Current open gaps after handoff-04

| Gap | Current lab evidence | Production consequence | Required action |
|---|---|---|---|
| private branch/tag rulesets unavailable | private endpoints return plan-related HTTP 403; equivalent public rulesets passed | full private policy cannot be reproduced on the current plan | obtain suitable plan capability or formally approve and test a lower-fidelity private fallback |
| K06 grouped PEP 508 Git update | extraction/lookup passed; live handoff-04 update lost `v` and split runtime/tooling branches | shared-source package refs could drift or fail lock generation | rerun only K06 against corrected `automation@1554ac4295daa4c75d983ddab0fca1442b33e675` |
| final static security rerun | actionlint passed; zizmor had one low documentation-only finding and zero medium/high | final workflow evidence should reflect the corrected inline permission comment | rerun actionlint/zizmor with K06 |
| Renovate lacks Workflows write by design | bounded selected-repository updater exists | normal Renovate cannot update workflow caller YAML | retain the dedicated publisher or approve broader permission separately |

Repository visibility is not an open functional gap. The report separately records private ordinary flows as PASS, private rulesets as plan-blocked and public rulesets as PASS.

## Gaps closed by handoff-04

- P04 promotion controller live success and duplicate-free rerun;
- T03 repeat bootstrap no-op and clean OpenTofu plan;
- K03 legacy answers, immutable `v0.4.3` release, real `uv.lock` change, green CI and Renovate idempotency;
- actionlint on the hardened workflow set;
- production/automerge/credential/visibility safety audits.

Previously closed evidence remains valid:

- private reusable workflow sharing and exact-SHA calls;
- private Renovate preset consumption and topic discovery;
- private Linux/macOS/Windows template acceptance;
- Release Please v0.4.0 through v0.4.3;
- OpenTofu repository creation and state recovery;
- root and nested lock regeneration;
- component wiring edge cases;
- restricted components credential negative/positive behavior;
- quality/policy parity and exact generated-baseline acceptance;
- wheel/sdist package chain and isolated installation.

## K06 correction

The handoff-04 live logs showed that `currentValue` incorrectly captured the literal `v`, while `extractVersionTemplate` normalized new tags to digits. Replacement therefore changed `@v0.32.3` to invalid `@0.32.4`. The group rule also matched aliases through `matchPackageNames`, although their aliases are `depName` and their shared package name is `betabitplus/py-lib-starter`.

The corrected preset:

- captures only the numeric version after a literal `v`;
- groups with `matchDepNames`;
- requires both dependencies with `minimumGroupSize: 2`;
- keeps `uv lock` as the exact post-upgrade task;
- includes a regression test for extraction, replacement, re-extraction and grouping.

## Existing production behavior to preserve

- private repositories;
- `dev → main` review flow;
- required CI and manual review;
- independent final-template releases;
- synchronized runtime/tooling refs while they share one root tag stream;
- `_api`/`_internal` architecture policy;
- immutable releases and rollback;
- selected-repository Apps;
- automerge disabled unless separately approved.

## Production migration exclusions

The experiment did not push to production, delete legacy code, modify production settings or secrets, install production Apps, create production refs, dispatch production workflows, or run Renovate/OpenTofu mutations against production.

## Conclusion

The production source is represented by the complete 25-command/127-module matrix. The target removes lifecycle mechanisms without requiring product-code rewrite. `lab-control#9` remains draft only for the K06 live rerun and final static check. The private-ruleset capability remains a rollout decision, not an untested implementation defect.
