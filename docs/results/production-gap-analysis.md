# Production gap analysis

## Baseline

- Frozen comparison baseline: `d59582375855cff69fb165e467dc5847bc75ca99`.
- All production snapshots remained unchanged.
- Production mutations during the experiment: **0**.

## Status

The isolated functional validation is complete. No functional acceptance ID remains open.

## Remaining rollout decisions

| Topic | Evidence | Decision needed before a private pilot |
|---|---|---|
| private branch and tag rulesets | private endpoints returned plan-related HTTP 403; equivalent public configurations passed | obtain suitable plan capability or approve and test a lower-fidelity private protection fallback |
| workflow caller updates | the bounded selected-repository publisher passed; ordinary Renovate intentionally has no Workflows write | retain the bounded publisher or approve a different permission model |
| migration sequencing | the lab platform is functionally validated; production was not changed | review an incremental pilot and rollback procedure repository by repository |
| repository visibility | ordinary private flows passed; the current lab repositories are public | use the intended private shape for a future pilot after choosing the protection mechanism |

## Closed functional paths

- P04: promotion controller succeeded twice with one promotion PR and no automerge.
- T03: repeat bootstrap was a no-op and the following OpenTofu plan was clean.
- K03: legacy answers updated through immutable `v0.4.3`, including a real lock change and green CI.
- K06: runtime and tooling moved together from `v0.32.3` to `v0.32.4` in one Renovate PR with `uv.lock`, green CI and an idempotent rerun.
- Final actionlint and pedantic/offline zizmor checks exited `0`.
- Production, automerge, credential and visibility audits passed.

## K06 evidence

- preset: `automation#1@1554ac4295daa4c75d983ddab0fca1442b33e675`;
- consumer PR: `sandbox-process#11`;
- head: `23180206f1df692ca3d0627edc69c86aadd19454`;
- files: `pyproject.toml`, `uv.lock`;
- `uv lock --check`: exit `0`;
- CI run `29487631571`: success;
- duplicate PRs after rerun: `0`;
- unrelated Renovate items changed: `0`.

## Production behavior to preserve

- private repositories;
- review-gated `dev → main` flow;
- required CI and manual review;
- independent immutable template releases;
- synchronized runtime/tooling refs while they share one root tag stream;
- architecture policy checks;
- reversible rollout;
- selected-repository credentials;
- automerge disabled unless separately approved.

## Conclusion

The full 25-command/127-module disposition is supported by the lab evidence. No more local-agent validation is required. `lab-control#9` remains draft because the experiment does not authorize migration and the private-ruleset capability decision is still open.
