# Production-shaped template platform experiment: final result

```text
Architecture result:
    CONDITIONAL GO

Production repositories changed:
    0

Current custom lifecycle LOC:
    6,673

Projected required custom lifecycle LOC:
    151

Commands removable:
    8

Commands replaced:
    14

Commands retained:
    2 legacy commands collapsed into one 191-LOC policy checker

Main remaining risks:
    Private-repository rulesets are unavailable on the current GitHub plan.
    Private reusable-workflow sharing must be enabled and re-tested.
    Live topic discovery, OpenTofu no-drift, Release Please and lock-refresh
    evidence require lab-administrative execution that the primary environment
    cannot perform.
```

Date: 2026-07-15  
Organization: `betabitplus-template-lab`  
Frozen and current informational production baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`  
Implementation PR: [lab-control#9](https://github.com/betabitplus-template-lab/lab-control/pull/9)

## Executive answer

The target architecture is technically sound and removes the custom template/update engine, downstream registry, fleet synchronizer, manifest/build assembler and most quality wrappers from the delivery path. The evidence supports a **CONDITIONAL GO** for production design, not an unconditional rollout.

The condition is operational rather than architectural: the current lab account cannot apply rulesets to private repositories, and several acceptance items require a lab-only administrative identity and locally installed Renovate/OpenTofu tooling. The prepared implementations are bounded and reviewable; unexecuted checks are explicitly marked `DEFERRED` rather than represented as passes.

The minimum owned surface is:

1. one 191-LOC stdlib-only policy checker for genuinely organization-specific Python conventions;
2. a 15-LOC repository bootstrap coordinator;
3. a 26-line idempotent `dev → main` promotion workflow;
4. an 11-line Renovate dry-run/digest guard;
5. a 99-line optional trusted workflow-ref updater because the main Renovate App intentionally has no Workflows permission;
6. a 12-line generic component wiring check.

The first three mandatory lifecycle items total **52 substantive lines**. Including the preferred separate workflow updater produces **151 custom lifecycle lines**. The generic wiring guard adds 12 lines and the unique policy checker adds 191, for an exact executable non-product surface of **354 lines**. This is a 96.9% reduction from the current 11,466 root/tooling source LOC and a 97.7% reduction from the 6,673 LOC strict lifecycle subset.

## 1. What was checked

- Frozen-source inventory of all requested root, tooling, runtime, scripts, workflows, actions, components, manifests and generated builds.
- Every published root and `py-lib-tooling` command, entry point, implementation group, tests, responsibility and replacement.
- Current versus projected LOC, excluding tests and generated fixtures from production logic.
- Official capabilities of Copier, Renovate, GitHub Actions/rulesets/Apps, OpenTofu GitHub provider, Release Please and the requested Python quality/package tools.
- Central Renovate preset design, topic-based discovery controller and allowlisted lock refresh.
- Private reusable workflow design and a real caller PR using an exact commit SHA.
- `dev → main` caller/process design with an idempotent promotion PR workflow.
- Two-phase OpenTofu repository provisioning design.
- Release Please design with acceptance gating and exact-SHA verification.
- Component add/remove/rename wiring semantics and the necessity of `WIRING.json`.
- Private credential model and current token/log hygiene.
- Direct community-tool replacements for quality and packaging wrappers.
- Residual architecture policy and `py-lib-runtime` classification.
- Fleet visibility decomposition and supply-chain hardening.

## 2. First-stage evidence intentionally not repeated

The first stage remains authoritative for:

- three independent Copier templates;
- exact-SHA private components submodules;
- Renovate submodule and Copier PRs;
- grouped nested Copier relationships;
- preservation of user changes and visible conflicts;
- one-gitlink rollback;
- Linux/macOS/Windows private checkout/render;
- production mutations equal to zero.

The deliberate conflict PR remains open and unmerged: [sandbox-python-lib#3](https://github.com/betabitplus-template-lab/sandbox-python-lib/pull/3). Existing tags `v0.1.0`, `v0.2.0`, `v0.3.0`, C1/C2/C3 commits, artifacts, `results.md` history and ADR 0001 were not rewritten.

## 3. New positive results

### Security and isolation

The local handoff proved that the final Renovate installation token sees exactly the eight lab repositories and has no production push/admin access. The previously unrotated App private key was replaced, all old keys were deleted, a new installation token succeeded, and current logs/artifacts were scanned: 536 files, 26.8 MB and zero credential findings.

### Inventory and replacement proof

`replacement-matrix.json` covers 127 production modules and all 25 published commands. Current source totals are:

| Surface | LOC |
|---|---:|
| `src/py_lib_starter` | 4,692 |
| `py-lib-tooling` | 6,774 |
| strict template/update lifecycle subset | 6,673 |
| registry/fleet | 841 |
| onboarding | 1,827 |
| quality/smoke wrappers | 711 |
| old unique-policy candidate | 968 |
| `py-lib-runtime` product library | 2,133 |

### Minimal policy

The prototype is one dependency-free CLI/pre-commit hook. It covers only conventions not adequately represented by import-linter/Ruff/Pyright: console entry-point routing through `_api.cli`, declaration-only root initializers, literal dynamic private imports, `# %%` examples, and the required directory/docs skeleton. Six unit tests pass.

### Reusable workflow implementation

A private `workflow_call` implementation was committed at `lab-control@8947060677a2f051351a56df48d6f50f37a37987`. A 12-line exact-SHA caller was opened as [sandbox-python-platform#3](https://github.com/betabitplus-template-lab/sandbox-python-platform/pull/3). The existing downstream validation run `29371632671` passed, proving the caller commit itself preserved the downstream template state.

### Declarative platform implementation

The experiment branch contains:

- four Renovate presets and a guarded topic-discovery controller;
- reusable library CI and template acceptance workflows;
- idempotent promotion PR and bounded trusted workflow updater;
- OpenTofu repository, branch, topic, variable, App-access and optional ruleset resources;
- a two-phase Copier bootstrap;
- Release Please configuration and exact-SHA guard;
- direct quality and packaging toolchain;
- generic component wiring checks.

Static validation passed for JSON, JSON5 preprocessing, YAML parsing, Python compile/tests and shell syntax.

## 4. New negative results

### Private rulesets are unavailable on the current plan

Every private lab repository returned HTTP 403 with GitHub's plan-upgrade/public-visibility message. This is not an OpenTofu/provider defect. The production target requires either a GitHub plan that exposes private rulesets or an explicitly accepted branch-protection fallback with reduced parity.

### Private reusable workflow call currently fails before creating jobs

The caller run `29371633018` failed with an empty job list. Because the referenced workflow file exists at the exact SHA and the downstream validation passed, the strongest inference is that private workflow sharing/access for the source repository is not enabled. This is useful negative evidence: repository content alone is insufficient; provisioning must enable Actions access for private callers. The PR remains unmerged.

### Live administrative checks remain unexecuted

Handoff 01 intentionally did not install/run Renovate, OpenTofu, actionlint or zizmor, did not create repositories, did not change topics/default branches/rulesets, and did not dispatch releases. The primary environment subsequently ran `zizmor 1.27.0`; its first audit found injection/credential/permission problems, those workflows were corrected, and the final offline regular audit reports zero findings. Those constraints prevented honest live acceptance for topic discovery, no-drift provisioning, `dev → main`, Release Please, lock refresh, tag protection and restricted-credential failure.

## 5. Selected community tools

| Responsibility | Selected mechanism | Custom implementation removed |
|---|---|---|
| project generation/update/conflicts | Copier CLI and answers file | template answer/check/update wrappers |
| component updates | Renovate `git-submodules` | component sync/orchestration |
| downstream template updates | Renovate `copier` | fleet sync and custom update engine |
| dependencies/locks | Renovate managers + exact `uv lock` post task | shared ref normalizer/lock controller |
| repository discovery | topics + Renovate autodiscovery | downstream registry |
| CI distribution | private reusable workflows | copied workflow bodies |
| repository settings | OpenTofu GitHub provider | Python onboarding API subsystem |
| releases | Release Please + required acceptance + exact-SHA guard | custom release controller |
| import architecture | import-linter + Ruff/Pyright | most project-structure checker code |
| metrics/audit | radon, flake8 plugins, pip-audit directly | quality wrappers |
| package verification | uv, twine, check-wheel-contents, check-manifest | custom smoke modules |
| workflow lint/security | actionlint + zizmor | ad-hoc workflow validation |

## 6. Rejected candidates

- Backstage and similar developer portals: excessive service/infrastructure for a small repository fleet.
- A new manifest assembler or generic platform framework: recreates the lifecycle engine being removed.
- Copier tasks for routine lock refresh: executable-template trust surface is broader than the exact allowlisted Renovate command.
- Giving the main Renovate App Workflows write: unnecessary privilege if the bounded updater remains small and review-gated.
- Persistent PATs: GitHub App installation tokens provide shorter lifetime and repository selection.
- A mandatory central fleet service: Renovate dashboards, PR/check status and OpenTofu plans already expose delivery health.

## 7. Replacement matrix

The authoritative machine-readable matrix is [`replacement-matrix.json`](replacement-matrix.json); the human view is [`replacement-matrix.md`](replacement-matrix.md). Summary:

| Classification | Commands | Modules |
|---|---:|---:|
| DELETE | 8 | 44 |
| REPLACE | 14 | 40 |
| RETAIN_MINIMAL | 2 → one checker | 6 |
| PRODUCT_LIBRARY | 0 | 26 |
| DEFER | 1 | 11 |

## 8. Residual custom surface

The exact responsibility, LOC, dependency and maintenance decision is in [`minimal-custom-surface.md`](minimal-custom-surface.md). No retained component implements template generation, Copier update, fleet membership, repository APIs, package release orchestration or runtime configuration.

## 9. Permission model

The least-privilege model is documented in [`permission-model.md`](permission-model.md). Key decision: main Renovate does **not** receive Workflows permission. Workflow ref changes are applied by a separate selected-repository App through a bounded updater that can only replace one exact SHA in one workflow file and opens a reviewable PR.

## 10. Production target architecture

ADR 0002 records the target:

```text
private components repository
        ↓ exact gitlink
independently released Copier templates
        ↓ Renovate Copier PR
downstream dev branch
        ↓ reusable CI + required review
promotion PR
        ↓
main
```

OpenTofu owns repository configuration; GitHub owns policy/CI execution; Renovate owns discovery and PR creation; Copier owns generation and three-way updates; Release Please owns release PR/changelog/tag; optional `py-lib-policy` owns only organization-specific static conventions.

## 11. Production rollout prerequisites

1. Obtain private rulesets capability or approve a documented lower-fidelity branch-protection fallback.
2. Create production Apps with selected-repository installation and the permission split in `permission-model.md`.
3. Publish automation workflows and Renovate presets, enable private workflow access and pin immutable refs.
4. Execute all Renovate dry stages against a production-shaped non-production organization.
5. Apply OpenTofu to one representative repository and require a clean second plan.
6. Complete Release Please, lock refresh, negative private-access and tag immutability checks.
7. Review the migration plan and rollback criteria before any production mutation.

## 12. Migration plan without executing production migration

1. Inventory production repository settings and current generated workflow divergence read-only.
2. Establish automation/components/template repositories and Apps.
3. Import or model one pilot repository in OpenTofu without changing application code.
4. Add topics, minimal Renovate config and thin workflow callers through normal PRs to `dev`.
5. Establish `.copier-answers.yml` baseline and run a no-change Copier verification.
6. Enable Renovate dry discovery, then one live pilot PR with automerge off.
7. Promote pilot `dev → main` manually after required checks/review.
8. Observe at least one component, template, package and workflow-ref update cycle.
9. Expand repository by repository; never mass-switch the fleet in one operation.
10. Delete legacy registry/assembler/tooling only after the last consumer has left it.

## 13. Rollback plan

- Component regression: revert the template gitlink to the previous exact commit.
- Template regression: pin downstream answers to the previous immutable template tag and run Copier update/revert PR.
- Reusable workflow regression: revert the exact caller SHA.
- Repository configuration regression: revert the OpenTofu configuration and apply after reviewing the plan.
- Release regression: never move/delete published tags; publish a corrected next version.
- Migration regression: remove the managed topic and disable repository-local Renovate config; existing code remains ordinary Git history.

## 14. Known limitations

- Rulesets on private lab repositories are blocked by the current plan.
- Private reusable-workflow access has not yet been enabled; current run is intentional negative evidence.
- Provider configuration is static-validated, not yet live-applied.
- `actionlint 1.7.12` was not available in the primary environment; `zizmor 1.27.0` was run successfully with zero final findings.
- A runtime replacement study can simplify individual `py-lib-runtime` helpers later, but the package is not lifecycle/platform code and does not block this architecture decision.
- The optional running-loop utility is deliberately deferred from platform architecture.

## 15. Exact evidence

- Implementation and reports: [lab-control#9](https://github.com/betabitplus-template-lab/lab-control/pull/9)
- Reusable caller negative/positive downstream evidence: [sandbox-python-platform#3](https://github.com/betabitplus-template-lab/sandbox-python-platform/pull/3)
- Reusable caller workflow run: `29371633018` — failure before jobs
- Downstream validation on the same commit: `29371632671` — success
- Existing conflict evidence: [sandbox-python-lib#3](https://github.com/betabitplus-template-lab/sandbox-python-lib/pull/3), run `29353371296`
- First-stage rollback acceptance: run `29353504047`
- Frozen/current production source: `d59582375855cff69fb165e467dc5847bc75ca99`
- Handoff security evidence: `docs/evidence/handoff-01-summary.json` in the experiment branch
- Machine-readable final status: [`final-experiment-results.json`](final-experiment-results.json)

## Final decision rule

The experiment succeeds at its principal architectural objective: custom code is no longer required for template assembly/update, registry membership, fleet synchronization, repository APIs, routine dependency freshness, CI distribution or generic quality tooling. The remaining code expresses only organization policy or coordinates mature tools.

The release is **CONDITIONAL GO** until the explicitly listed private-plan and live-administration acceptance gaps are closed. No production migration has started.
