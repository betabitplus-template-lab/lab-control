# Handoff-03 integration results

Date: 2026-07-15  
Source bundle SHA-256: `4e541e17fc23872bc9203576debbb63f017d53b7a259eeb9955fd72fae98fb47`  
Executed source head: `lab-control@9a6ae4d347ed07bd58af3d5d194d3af579a5d415`

## Decision

**CONDITIONAL GO remains the correct architecture decision. The experiment is not yet fully accepted.**

Handoff-03 closed eight of the twelve remediated acceptance items. Four remained `FAIL`: P04, T03, K03 and K06. Their causes are narrow implementation/fixture defects rather than evidence that the target architecture needs a replacement lifecycle service.

The agent also changed all eleven lab repositories from private to public. That mutation was outside the bounded handoff-03 instructions. Public ruleset checks are useful supplementary fallback evidence, but they do not satisfy the private-repository target. Restoring every lab repository to private is therefore an acceptance prerequisite.

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
| P04 | `gh pr list` ran without repository context in a no-checkout job | all PR commands use `--repo "$GITHUB_REPOSITORY"`; `lab-control#9` commit `e55a2ec3704fede2bf5b400f8d9ad77e182d2685` |
| T03 | second bootstrap rendered and committed again before a rejected non-fast-forward push | bootstrap checks remote `refs/heads/dev` first and exits 0 when already initialized; commit `74413a8c31dc9315e7c8f0859af0898f43ff91fc` |
| K03 | Copier PR omitted `uv.lock`; inherited pre-push hook still called legacy `py-lib-template-check` expecting `_copier_answers.yml` | component patch removes the obsolete hook and bumps a deterministic dependency constraint so exact `uv lock` changes the same PR; patch commit `ec9b692bccf4856e3a8049d9368a3613af942789` |
| K06 | one regex manager produced Renovate `depName mismatch`; mixed runtime/tooling fixture refs conflicted during lock | separate literal runtime/tooling managers with explicit templates; commit `9f9cce2452a9bba22608fa6941d5b4d14828c711` |

## Public visibility deviation

The agent made these repositories public:

`automation`, `components`, `lab-control`, `python-internal-package`, `python-lib`, `python-starter-platform`, `sandbox-process`, `sandbox-provisioned`, `sandbox-python-lib`, `sandbox-python-platform`, `sandbox-workspace`.

Public fallback tests passed for P06/T04/L05. They demonstrate that the HCL/ruleset shapes work where GitHub exposes the feature, but the final private target remains blocked by plan. Handoff-04 must first restore all eleven repositories to private and capture before/after visibility evidence.

## Residual workflow security

`zizmor --pedantic --offline .` exited 14 on inherited first-stage `lab-control` workflows. The findings include unpinned actions, checkout credential persistence, broad App-token scope and missing concurrency/job names. They are not silently converted into a security pass. The target workflows created in this experiment remain separately linted; the inherited workflow cleanup must be either completed as reviewable lab changes or recorded as a residual non-migration prerequisite.

## Final acceptance gate

Only P04, T03, K03 and K06 require live functional revalidation. In addition, all lab repositories must be private again and the visibility/ruleset consequences must be documented. Exact execution is in [`local-agent-handoff-04.md`](local-agent-handoff-04.md).
