# Production gap analysis

## Baselines

- Frozen comparison baseline: `d59582375855cff69fb165e467dc5847bc75ca99`.
- Informational current `dev` HEAD at handoff time: the same SHA.
- These baselines are not mixed.
- Production mutations during both experiment stages: **0**.

## Capability gaps

| Gap | Lab evidence | Production consequence | Required decision |
|---|---|---|---|
| private repository rulesets unavailable | all eight private repos return HTTP 403 | target branch/tag policy cannot be reproduced on current plan | enable suitable GitHub plan or accept/test branch-protection fallback |
| private workflow access not enabled | caller run fails before jobs | thin callers cannot use central private automation yet | enable source repository Actions access and re-test |
| Renovate lacks Workflows write | confirmed App permissions | normal Renovate cannot update caller YAML | use separate selected-repo workflow publisher (recommended) or explicitly grant permission |
| no live OpenTofu run | tofu absent/prohibited in handoff 01 | no no-drift proof | run two-phase representative provisioning |
| no live topic autodiscovery | topic/admin changes unavailable | registry deletion not yet live-proven | positive/negative/disabled topic matrix and dry/full run |
| no live Release Please | release identity/tag policy unavailable | custom controller replacement not end-to-end proven | run v0.4 line in one template |
| no live lock refresh | Renovate live prohibited | shared lock helper replacement not end-to-end proven | dependency-changing template release and `uv lock --check` |
| restricted components credential unavailable | credential creation unavailable | negative private-access boundary not demonstrated | create temporary read-without-components token and test |
| actionlint unavailable; zizmor completed | final zizmor audit has 0 findings; actionlint binary unavailable | one independent syntax checker still missing | run actionlint 1.7.12 in handoff 02 |

## Existing production behavior to preserve

- private repositories;
- `dev → main` review flow;
- required CI and manual review;
- independent final-template versions;
- ordinary versioned runtime dependency;
- `_api`/`_internal` architecture policy;
- immutable releases and rollback;
- centralized dependency updates;
- selected-repository Apps.

## Production migration exclusions

This experiment does not push to production, delete legacy code, modify settings/secrets, install Apps, create production branches/PRs/tags, dispatch workflows or run Renovate against production. The result is a design and lab evidence set, not a migration.

## Read-only audit conclusion

The current production source is sufficiently represented by the full module/command matrix. The target removes lifecycle mechanisms without requiring product-code rewrite. Migration should be incremental per repository and preserve an immediate disable/topic/ref rollback.
