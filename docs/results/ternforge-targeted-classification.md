# Ternforge targeted validation: question classification

Date: 2026-07-17  
Baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`

Statuses follow the requested meanings: `DOC-CONFIRMED`, `LAB-CONFIRMED`, `NEEDS-EXPERIMENT`, `OUT-OF-SCOPE`.

| Question | Status | Reason and exact remaining uncertainty |
|---|---|---|
| Exact-SHA components submodule under `template/_components` | LAB-CONFIRMED | Previous lab rendered and updated exact gitlinks. Do not repeat the generic mechanism. |
| Whole common file through symlink | LAB-CONFIRMED | Previous Linux/macOS/Windows evidence covers text/binary/empty symlinks. New fixture only demonstrates the selected responsibility path. |
| Multiple components contributing distinct `.agents/` files/subdirectories | NEEDS-EXPERIMENT | The mechanism is known, but the new responsibility-first ownership/layout and collision transparency were not exercised. |
| Final-template-owned compound file including several Jinja fragments | NEEDS-EXPERIMENT | Jinja include behavior is known; the new multi-fragment ownership boundary and validity of real `pyproject.toml`/`.gitignore` output need direct evidence. |
| No assembler/manifests/registry | LAB-CONFIRMED | Previous composed-template pilot already removed the runtime assembler and manifest engine. The new fixture must merely avoid reintroducing them. |
| No committed `WIRING.json` | NEEDS-EXPERIMENT | Old lab retained `WIRING.json`. A new acceptance based on one-owner paths, broken-symlink checks and rendered output must prove sufficient transparency. |
| Future extension to TS/service components | DOC-CONFIRMED | The responsibility-first directory taxonomy is structurally extensible; only a static path-reservation check is needed, not a separate live experiment. |
| Copier ordinary tags/answers/update/conflict semantics | LAB-CONFIRMED | Previous matrix and conflict PR already cover generic behavior. |
| Infra-template exact ownership and README preservation | NEEDS-EXPERIMENT | New minimal output surface and create-once README semantics were not tested together. |
| Deleted infra README during update | NEEDS-EXPERIMENT | Copier docs predict that a user-deleted path remains excluded, but the selected template must record direct behavior before any special rule is adopted. |
| Py-library user-owned directories preserved | NEEDS-EXPERIMENT | New ownership set (`src/tests/docs/examples/workbench/README`) and managed-file set require a real v0.1→v0.2 update snapshot. |
| Copier update without `--trust` | NEEDS-EXPERIMENT | Expected because no tasks/migrations/extensions are present; hosted Renovate must prove it. |
| Components submodule update by hosted Community Cloud | NEEDS-EXPERIMENT | Old lab used a different Renovate execution model. Release-tag-only semantics and `.gitmodules branch` behavior remain material. |
| Hosted Renovate Copier PR | NEEDS-EXPERIMENT | Must be a real Community Cloud PR in a public lab repo with no private token wiring. |
| Exact-SHA reusable workflow update at job-level `uses:` | NEEDS-EXPERIMENT | GitHub syntax and Renovate digest comments are documented, but actual hosted PR/CI behavior is required. |
| Versioned Renovate preset update | NEEDS-EXPERIMENT | Tagged presets are documented; automatic update of the pinned preset reference and strict validation need live evidence. |
| `tool.uv.sources` Git tag update with built-in PEP 621 | NEEDS-EXPERIMENT | Manager recognizes the field/lockfile, but Git-tag extraction/update is not unambiguously documented. Minimal regex is allowed only after an evidenced built-in failure. |
| Selected pre-commit hook updates | NEEDS-EXPERIMENT | Manager is beta and opt-in; selected hooks must generate a correct green PR. |
| Standalone runtime repository | NEEDS-EXPERIMENT | Old lab treated it as a package in the legacy workspace. Independent build/test and dependency boundaries were not proven. |
| Standalone policy repository | NEEDS-EXPERIMENT | Minimal policy logic exists and passed focused tests, but independent repository/dev-dependency use remains to prove. |
| Standalone testkit repository | NEEDS-EXPERIMENT | Replacement matrix marks VCR/console/image/e2e/fixture helpers for preservation; extraction and independent tests remain open. |
| Representative consumer with runtime/dev/test Git sources and frozen lock | NEEDS-EXPERIMENT | Previous grouped same-root Git dependency test differs from three separately tagged repositories. |
| OpenTofu repository bootstrap order | NEEDS-EXPERIMENT | Old OpenTofu fixture had different private-plan rules, two branch rulesets, approvals and extra variables. New public, approval-zero, two-phase configuration must be applied live. |
| Public branch/tag ruleset capabilities | DOC-CONFIRMED | GitHub documents availability and individual rules; exact combined configuration, bypass and bootstrap behavior still need the OpenTofu experiment. |
| `dev → main` source restriction | DOC-CONFIRMED | Rulesets target destination refs and do not enforce PR source branch. Record as workflow convention; do not build a promotion guard. |
| Minimal reusable Python CI commands | NEEDS-EXPERIMENT | Standard commands are not in doubt; exact thin caller→reusable workflow integration and required check identity need a live run. |
| Workflow-repository actionlint/zizmor/smoke | NEEDS-EXPERIMENT | New split `infra-ci` repository and privileged workflow set differ from old combined automation repository. |
| Components rollback | LAB-CONFIRMED | One-line gitlink rollback already passed. Re-run only for the new release-tag chain if needed to prove the hosted flow. |
| Copier PR close/revert rollback | NEEDS-EXPERIMENT | New hosted PR behavior should be recorded; no fleet action is allowed. |
| Reusable workflow SHA rollback | NEEDS-EXPERIMENT | One-file caller rollback is simple but should be demonstrated in the new split repository. |
| Git dependency tag/lock rollback | NEEDS-EXPERIMENT | Must show `uv.lock` returns to the previous exact commit and `uv sync --frozen` passes. |
| Ruleset disable/rollback through OpenTofu | NEEDS-EXPERIMENT | Must show recovery without manual multi-repository editing. |
| General Linux/macOS/Windows matrix | OUT-OF-SCOPE | Explicitly excluded; Ubuntu is sufficient except inherited evidence. |
| Full 127-module re-audit | OUT-OF-SCOPE | The replacement matrix is authoritative. Only the runtime/policy/testkit split is revisited. |
| Generic behavior of Ruff/Pyright/pytest/pre-commit/actionlint/OpenTofu | OUT-OF-SCOPE | Standard tool functionality is not the question. |
| Release Please broad re-evaluation | OUT-OF-SCOPE | Already evidenced and not a new uncertain chain in this targeted plan. |

## Accepted experiment order

1. Build the responsibility-first components and two final templates, then run local render/update acceptance.
2. Create released tags and only then enable hosted Renovate tests.
3. Establish split `infra-ci` and `infra-updates`, then test caller/preset updates.
4. Split runtime/policy/testkit and prove one frozen consumer.
5. Create the OpenTofu sandbox with rulesets disabled, establish branches/checks, then enable rulesets.
6. Run only the five targeted rollback checks.
7. Return raw evidence; the primary agent writes the final verdict.

## Fallback discipline

- Do not add `WIRING.json` unless a concrete one-owner ambiguity survives rendered-tree and broken-symlink checks.
- Do not add a custom submodule updater. If tag tracking fails, record the exact Renovate limitation and test only the smallest documented configuration change.
- Do not add a general regex framework. At most one literal regex manager may target the exact `tool.uv.sources.<name>.tag` field after built-in failure.
- Do not add a workflow publisher, self-hosted Renovate, phase controller, fleet registry, central API, custom CI image or permanent canary.
