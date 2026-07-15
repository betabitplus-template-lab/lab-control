# Production gap analysis

## Baselines

- Frozen comparison baseline: `d59582375855cff69fb165e467dc5847bc75ca99`.
- Informational current `dev` HEAD at both source audits: the same SHA.
- Production mutations during the complete experiment: **0**.
- The frozen baseline and current informational state are not mixed in the replacement matrix.

## Capability and acceptance gaps after handoff-02

| Gap | Current lab evidence | Production consequence | Required decision/action |
|---|---|---|---|
| private repository branch/tag rulesets unavailable | private endpoints return GitHub plan HTTP 403 | target branch/tag policy cannot be reproduced with current subscription | enable a suitable plan or formally accept/test a lower-fidelity branch-protection fallback |
| OpenTofu full flow not yet completed | handoff-02 stopped before repository creation on provider-schema validation; field corrected in `7f241a8d` | no two-phase/no-drift/recovery proof yet | run bounded handoff-03 provisioning against `sandbox-provisioned` only |
| corrected promotion controller not rerun | repository shape and one promotion PR passed; old controller used unauthenticated fetch; corrected in `d8ad5ad9` | idempotent automatic PR creation needs final run evidence | publish corrected automation SHA and rerun in `sandbox-process` |
| corrected private Copier clone path not rerun | reusable workflows pass; prepared template acceptance failed only in Copier's independent private clone; corrected in `51dcb45c` | central template acceptance/release caller needs final cross-platform proof | rerun Linux/macOS/Windows and one safe release line |
| legacy-answer update compatibility needs rerun | failure reproduced; default-compatible fix is `python-lib#19` | older managed repositories may otherwise fail on newly hidden questions | validate/merge fix and repeat Copier+lock PR |
| nested fixture acceptance needs rerun | both nested locks regenerated idempotently; fixture hardcoded v0.2.0; fix is `sandbox-workspace#8` | valid grouped updates can be falsely blocked | validate/merge dynamic same-semver test and repeat CI |
| PEP 508 Git dependency manager needs live proof | `pep621` does not extract tag; constrained regex manager authored in `8d055e49` | `py-lib-runtime`/`py-lib-tooling` ordinary PR behavior not yet proven | run extract/lookup/full and one live lab-only PR with `uv.lock` |
| corrected policy/packaging workflow needs real-baseline rerun | rule parity and wheel/sdist smoke passed; false positives/tool assumptions corrected | final deletion of wrappers should wait for exact prepared-chain evidence | run S03/D03/D05 subset in handoff-03 |
| Renovate lacks Workflows write by design | confirmed App permissions; bounded updater authored | normal Renovate cannot edit caller workflow YAML | keep separate selected-repository workflow publisher or explicitly accept broader permission |

## Gaps closed by handoff-02

The following are no longer open production-gap claims:

- private reusable workflow sharing and exact-SHA caller execution;
- Renovate private preset consumption;
- organization/topic autodiscovery, disabled-topic behavior, extract/lookup/full progression and live idempotency;
- Release Please release PR/tag/release production shape through v0.4.0 and v0.4.1;
- root and nested lock regeneration with private Git authentication;
- component add/wire/break/rename acceptance;
- restricted credential without components read, subsequent success and cleanup;
- direct quality-rule parity and residual-policy rule parity;
- wheel/sdist build and isolated installation smoke;
- actionlint/zizmor review of the reusable automation set.

## Existing production behavior to preserve

- private repositories;
- `dev → main` review flow;
- required CI and manual review;
- independent final-template versions;
- ordinary versioned runtime dependency;
- `_api`/`_internal` architecture policy;
- immutable releases and rollback;
- centralized dependency updates;
- selected-repository Apps;
- automerge disabled unless a future independent policy decision changes it.

## Production migration exclusions

This experiment does not push to production, delete legacy code, modify production settings/secrets, install production Apps, create production branches/PRs/tags, dispatch production workflows or run Renovate/OpenTofu against production. The result is a design and isolated-lab evidence set, not a migration.

## Read-only audit conclusion

The current production source is represented by the full module/command matrix. The target removes lifecycle mechanisms without requiring product-code rewrite. Migration must remain incremental per repository and retain immediate topic/config/ref rollback. `lab-control#9` stays draft until the exact handoff-03 remediation subset is green; private ruleset capability remains an explicit rollout gate.
