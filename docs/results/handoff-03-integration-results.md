# Handoff-03 integration results

Date: 2026-07-15  
Source bundle SHA-256: `4e541e17fc23872bc9203576debbb63f017d53b7a259eeb9955fd72fae98fb47`  
Executed source head: `lab-control@9a6ae4d347ed07bd58af3d5d194d3af579a5d415`

## Decision

**CONDITIONAL GO remains the correct architecture decision. The experiment is not yet fully accepted.**

Handoff-03 closed eight of the twelve remediated acceptance items. Four remained `FAIL`: P04, T03, K03 and K06. Their causes are narrow implementation/fixture defects rather than evidence that the target architecture needs a replacement lifecycle service.

The agent also changed all eleven lab repositories from private to public. That was outside the original bounded instruction, but the resulting evidence is still useful when interpreted correctly:

- private execution proved all tested private flows except private rulesets;
- private rulesets remain `BLOCKED` by the current GitHub plan;
- public execution proved that the same ruleset configurations work where the plan exposes the feature.

Repository visibility is therefore not a prerequisite for the remaining four functional checks. The final report must record private and public capability separately and must not claim that public evidence proves private ruleset availability.

## Immutable result

| Status | Count |
|---|---:|
| PASS | 8 |
| NEGATIVE_PASS | 0 |
| FAIL | 4 |
| BLOCKED in the 12 revalidated IDs | 0 |

Unchanged external blockers:

- P06 — private branch rulesets: `BLOCKED`;
- T04 — OpenTofu private ruleset phase: `BLOCKED`;
- L05 — immutable private release-tag ruleset: `BLOCKED`.

The original statuses are preserved in [`handoff-03-summary.json`](../evidence/handoff-03-summary.json).

## Safety audit

- production mutations: **0**;
- production baseline/dev/tags unchanged;
- automerge: **false** across 53 inspected PRs;
- `sandbox-python-lib#3`: open, unmerged and unchanged;
- private key files found: **0**;
- credential-pattern findings after redaction: **0**;
- OpenTofu-state credential findings: **0**.

## Newly accepted live evidence

- S03: all four requested actionlint invocations exited 0.
- S04: OpenTofu init/fmt/validate passed with provider 6.6.0.
- R03/T01: `sandbox-provisioned` was created only by OpenTofu, initially verified private, and archived through cleanup.
- L04: private Linux/macOS/Windows acceptance passed; Release Please published `python-lib@v0.4.2` at exact commit `2940bc355da2a957e0deb6c1660ce57293e9674b`, release `354387791`.
- K05: `sandbox-workspace#8` merged; PR #5 passed with two equal `v0.2.1` answers and idempotent nested locks.
- D03: both corrected and preserved legacy policy checks accepted the exact baseline `d594c0dd80908f89bc5a534681f27765fb985c4b`.
- D05: direct package chain passed; wheel SHA-256 `d0a4f11f563aeded804fd86ecf82e576f3d1589b454b62055a55223c35553041`, sdist SHA-256 `b88e32fd2068ec8aab65fe9f07a21cc4bfb2c00aeb00ac160369a3ab01933fcc`.

## Remaining failures and corrections

| ID | Handoff-03 failure | Correction now in review |
|---|---|---|
| P04 | `gh pr list` ran without repository context in a no-checkout job | all PR commands use `--repo "$GITHUB_REPOSITORY"`; current `lab-control#9` branch |
| T03 | second bootstrap rendered and committed again before a rejected non-fast-forward push | bootstrap checks remote `refs/heads/dev` first and exits 0 when already initialized; current `lab-control#9` branch |
| K03 | Copier PR omitted `uv.lock`; inherited pre-push hook still called legacy `py-lib-template-check` expecting `_copier_answers.yml` | component patch removes the obsolete hook and changes a deterministic dependency constraint so exact `uv lock` changes the same PR; `experiments/remediation/k03-components.patch` |
| K06 | one regex manager produced Renovate `depName mismatch`; mixed runtime/tooling fixture refs conflicted during lock | separate literal runtime/tooling managers with explicit dependency names, grouped into one shared-root-tag update; current `lab-control#9` branch |

## Access policy for the final run

The remaining work may use the existing broad credential inside `betabitplus-template-lab/*`. No new App, PAT, SSH key or deploy key is required. The hard boundary is zero production writes.

## Residual workflow security

`zizmor --pedantic --offline .` exited 14 on inherited first-stage `lab-control` workflows. Those workflows were subsequently hardened in the experiment branch with exact action SHAs, selected-repository App-token scopes, explicit permissions, disabled checkout credential persistence, temporary askpass, concurrency and named jobs.

The current branch requires one fresh actionlint and pedantic zizmor run. Findings must not be suppressed merely to obtain a green result.

## Final acceptance gate

Only P04, T03, K03 and K06 require live functional revalidation. Exact execution is in [`local-agent-handoff-04.md`](local-agent-handoff-04.md).