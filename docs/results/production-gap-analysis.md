# Production gap analysis

## Baselines

- Frozen comparison baseline: `d59582375855cff69fb165e467dc5847bc75ca99`.
- Informational current production `dev` HEAD at every audit: the same SHA.
- Production mutations during all experiment stages: **0**.
- Frozen baseline and informational current state are not mixed.

## Current gaps after handoff-03

| Gap | Current lab evidence | Production consequence | Required decision/action |
|---|---|---|---|
| private branch/tag rulesets unavailable | private endpoints return plan-related HTTP 403 | target private policy cannot be reproduced on the current plan | enable suitable capability or formally approve/test a lower-fidelity private fallback |
| lab visibility must be restored | handoff-03 changed all 11 lab repositories to public for supplementary fallback tests | final lab state no longer matches the private production target | preserve fallback evidence, remove only recorded fallback controls and restore all repositories to private first |
| P04 promotion workflow live rerun | repository shape and single promotion PR exist; handoff-03 failed only because `gh pr list` lacked `--repo` | final idempotent automation proof remains open | publish current exact automation SHA and require successful duplicate-free rerun |
| T03 bootstrap repeat guard | OpenTofu creation/apply/no-drift/import passed; old repeat bootstrap authored another local commit | recovery/operator reruns need a clean no-op | run corrected remote-ref guard twice and prove remote SHAs unchanged |
| K03 legacy-answer lock PR | legacy answers update and CI worked, but PR lacked `uv.lock` and retained a legacy wrapper hook | older consumers cannot yet prove one atomic Copier+lock update | release exact component patch, then require answers/config/pyproject/lock in one green PR |
| K06 PEP 508 live update | dry extraction found runtime/tooling; old live run had `depName mismatch` and invalid mixed refs | ordinary shared Git package update is not yet end-to-end proven | publish literal managers and require one grouped shared-root-tag PR with `uv.lock` |
| whole-repository workflow security rerun | handoff-03 pedantic zizmor found inherited workflow issues; current PR hardens them | final workflow baseline needs independent zero-exit evidence | actionlint all workflows and run `zizmor --pedantic --offline` on current PR head |
| Renovate lacks Workflows write by design | selected-repository trusted updater exists | main Renovate cannot directly edit workflow caller YAML | retain the dedicated bounded publisher or separately approve broader privilege |

## Gaps closed by live evidence

The following are no longer open claims:

- private reusable workflow sharing, exact-SHA calls, failure and cancellation propagation;
- private Renovate preset consumption, organization/topic discovery and live idempotency;
- OpenTofu repository-only creation through the private first phase;
- private Linux/macOS/Windows template acceptance;
- Release Please v0.4.0, v0.4.1 and v0.4.2 exact target releases;
- root lock baseline and nested lock idempotency;
- nested workspace dynamic semver acceptance;
- component add/wire/break/rename behavior;
- restricted credential negative/positive components access;
- direct quality parity and residual policy parity;
- exact generated-baseline policy acceptance;
- direct wheel/sdist packaging and isolated installation.

## Public fallback interpretation

Public P06/T04/L05 fallback tests passed and proved the policy resource shapes where GitHub exposes them. They remain supplementary only. They do not convert private P06/T04/L05 from `BLOCKED` to `PASS`, and they do not justify leaving lab repositories public.

## Existing production behavior to preserve

- private repositories;
- `dev → main` review flow;
- required CI and manual review;
- independent final-template releases;
- ordinary versioned runtime/tooling dependencies;
- `_api`/`_internal` architecture policy;
- immutable releases and rollback;
- centralized dependency updates;
- selected-repository Apps;
- automerge disabled unless a separate future decision changes it.

## Production migration exclusions

This experiment does not push to production, delete legacy production code, modify production settings/secrets, install production Apps, create production branches/PRs/tags, dispatch production workflows or run Renovate/OpenTofu against production. It is a design and isolated-lab evidence set, not a migration.

## Read-only audit conclusion

The production source is represented by the complete 25-command/127-module matrix. The target removes lifecycle mechanisms without requiring product-code rewrite. Migration must remain incremental and preserve immediate topic/config/ref rollback. `lab-control#9` stays draft until handoff-04 is green and all lab repositories are private; private ruleset capability remains an explicit rollout gate.
