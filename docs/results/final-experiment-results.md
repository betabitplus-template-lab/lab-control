# Production-shaped template platform experiment: final result

Date: 2026-07-15  
Organization: `betabitplus-template-lab`  
Frozen/read-only production baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`  
Primary implementation: [lab-control#9](https://github.com/betabitplus-template-lab/lab-control/pull/9)

```text
Architecture result:
    CONDITIONAL GO

Production repositories changed:
    0

Current root + tooling custom source:
    11,466 LOC

Current strict template/update lifecycle:
    6,673 LOC

Projected required custom lifecycle:
    <= 151 LOC

Projected unique policy checker:
    196 LOC

Projected executable non-product custom surface:
    <= 359 LOC

Published commands:
    8 delete
    14 replace
    2 collapse into one policy checker
    1 optional developer utility deferred
```

## Executive conclusion

The target architecture is sound. Mature tools can own template generation and three-way updates, dependency and component PRs, repository discovery, reusable CI, repository configuration, releases, locks and generic quality/package checks. The custom template/update engine, registry, fleet synchronizer, repository API subsystem and most wrappers are not required in the target delivery path.

The result remains **CONDITIONAL GO**, not unconditional GO, for two reasons:

1. private branch/tag rulesets return GitHub plan-related HTTP 403;
2. handoff-02 found implementation defects that have been corrected but still require bounded live revalidation before the main experiment PR can leave draft.

No production migration has started. All writes were restricted to `betabitplus-template-lab/*`.

## Handoff-02 scorecard

The returned handoff-02 bundle has SHA-256 `5894d7468d2a5473e44c649fccebbff139c79f391b044014992de495b1ef18d6` and contains 370 evidence files.

| Status | Count |
|---|---:|
| PASS | 40 |
| NEGATIVE_PASS | 6 |
| FAIL | 10 |
| BLOCKED | 5 |

The original statuses are preserved in [`handoff-02-report.json`](../evidence/handoff-02-report.json). The exact interpretation and remediation mapping is in [`handoff-02-integration-results.md`](handoff-02-integration-results.md).

Safety invariants remained true:

- production mutations: `0`;
- automerge enabled: `false`;
- `sandbox-python-lib#3`: open and unmerged;
- old v0.1.0-v0.3.0 tags and C1/C2/C3 evidence: unchanged;
- temporary credentials: revoked;
- disclosed credential findings: `0`.

## Live evidence now proved

### Private reusable workflows

The private `automation` repository was created and published at `a5cd8112c8e8b221dceb397c1e882a9a25148b86`, tag `v0.1.0`. Organization access for private callers was enabled.

- Linux/macOS, inherited-secret and read-only caller verification: run `29375576270`;
- intentional failure propagation: run `29375625874`;
- cancellation propagation: run `29375658789`;
- tagged ref: run `29375727768`;
- final exact-SHA ref: run `29375763651`.

The caller remains reviewable in `sandbox-python-platform#3`; automerge is disabled.

### Renovate private presets and fleet discovery

The private base/template/downstream/workspace presets were published and consumed. Explicit allowlist `extract`, `lookup` and `full` phases passed. Organization/topic discovery selected the expected managed, template, downstream, workspace and untagged fixtures while skipping the disabled repository. One reviewed live run created the expected PRs; rerun created no duplicates. All observed Renovate PRs had `auto_merge=null`.

This proves that GitHub topics plus repository-local `.copier-answers.yml` relationships can replace the custom downstream registry for delivery operations.

### `dev → main` repository shape

`sandbox-process` was bootstrapped with `dev` as default and `main` as the promotion baseline. A safe update PR passed CI and merged to `dev`: `sandbox-process#1`, run `29376918751`. Exactly one promotion PR remained open: `sandbox-process#2`.

The initially prepared promotion workflow failed because it removed checkout credentials and then executed an unauthenticated `git fetch`. The corrected workflow uses the authenticated GitHub compare and PR APIs and no checkout. Its live rerun is assigned to handoff-03.

### Release Please

Release Please produced two real patch lines without rewriting historical tags:

| Release | Main/tag target | Release ID |
|---|---|---:|
| `python-lib@v0.4.0` | `0477653722f8a8b125e2bd3963b37d4a0d10c153` | `354133543` |
| `python-lib@v0.4.1` | `1a4fabe2c0449c5fe92d745eea0f9494c6fed160` | `354137656` |

Conventional commits, release PRs, acceptance gating, tags and GitHub releases were exercised. The prepared reusable acceptance workflow exposed a private Copier temporary-clone authentication gap. The workflow now supplies only an ephemeral masked Git URL rewrite on Linux/macOS/Windows and retains `persist-credentials:false`; the exact-SHA release guard now uses the GitHub API and handles annotated/lightweight tags.

### Locks and ordinary dependencies

- exact `uv.lock` baseline and CI: `sandbox-process#3`, run `29377905812`;
- a real setuptools change flowed components → template release → downstream;
- both nested workspace locks regenerated idempotently with private Git authentication;
- unrelated lock state remained stable.

Two fixture/manager gaps were found and corrected:

- old answers omitted the later hidden `template_profile`; compatibility fix: draft `python-lib#19`;
- nested acceptance hardcoded historical `v0.2.0`; dynamic same-semver fix: draft `sandbox-workspace#8`;
- PEP 508 Git dependencies were not extracted by `pep621`; a constrained Renovate regex manager now covers only `py-lib-runtime` and `py-lib-tooling`, backed by GitHub tags and the exact `uv lock` post task.

### Component wiring edges

The experiment exercised:

- new component file with no implicit template output;
- explicit symlink/output wiring;
- broken-symlink negative case;
- rename case;
- generated audit of 165 symlinks with zero broken links in the final positive state.

A generic filesystem/git check is sufficient. A custom lifecycle registry such as `WIRING.json` is not required.

### Private access negative test

A temporary credential that could read template/downstream repositories but not components failed recursive private clone as expected. Adding components read succeeded. All temporary deploy keys were revoked and private key files removed. This validates the separate components-read requirement without broadening the main credential.

### Tooling reduction

- legacy/direct quality behavior: 8/8 parity;
- residual policy rules: 12/12 parity;
- wheel and sdist build, metadata checks and isolated installs: pass;
- reusable workflow actionlint/zizmor review: pass.

Handoff-02 correctly found that the first direct packaging workflow assumed `twine` and `check-wheel-contents` existed in the project environment and omitted `.copier-answers.yml` from check-manifest. The corrected workflow runs pinned tools through `uvx` and explicitly ignores only the Copier answers file.

The minimal policy checker was corrected to accept the generated `PackageNotFoundError` version fallback and to exempt example-package `__init__.py` files from the `# %%` notebook-cell convention. Eight local tests pass; live real-baseline parity is assigned to handoff-03.

## Replacement inventory

The authoritative machine-readable matrix is [`replacement-matrix.json`](replacement-matrix.json); the human view is [`replacement-matrix.md`](replacement-matrix.md). It covers all 25 published commands and 127 production modules.

| Classification | Commands | Result |
|---|---:|---|
| DELETE | 8 | no compatibility wrapper retained |
| REPLACE | 14 | mature tool/direct command owns responsibility |
| RETAIN_MINIMAL | 2 → 1 checker | organization-specific static conventions only |
| DEFER | 1 | optional running-loop developer utility outside platform architecture |

Source inventory:

| Surface | LOC |
|---|---:|
| `src/py_lib_starter` | 4,692 |
| `py-lib-tooling` | 6,774 |
| strict lifecycle subset | 6,673 |
| registry/fleet | 841 |
| onboarding | 1,827 |
| quality/smoke wrappers | 711 |
| old unique-policy candidate | 968 |
| `py-lib-runtime` product library | 2,133 |

`py-lib-runtime` is a product/runtime library, not platform lifecycle machinery. It remains independently versioned and updated as an ordinary dependency. Individual helpers can be studied later, but its 2,133 LOC are excluded from the platform-lifecycle reduction denominator.

## Target architecture

```text
private components repository
        ↓ exact gitlink
independently released Copier templates
        ↓ Renovate Copier PR + exact uv lock
downstream dev branch
        ↓ private reusable CI + required review
single idempotent promotion PR
        ↓
main
```

Ownership boundaries:

- Copier: generation and three-way downstream update/conflicts;
- Renovate: submodule, Copier, package, workflow-ref discovery and PR creation;
- GitHub topics: fleet membership/lane metadata;
- reusable Actions workflows: CI/acceptance distribution;
- OpenTofu: repository settings, branches, topics, variables and App installation access;
- Release Please: release PR, changelog, tag and release;
- direct community tools: quality, security and package verification;
- optional `py-lib-policy`: only conventions generic tools cannot express.

The main Renovate App does not receive Workflows write permission. A separate selected-repository publisher may perform one bounded exact-SHA replacement and open a reviewable PR.

## Remediated failures requiring handoff-03

| IDs | Corrected location |
|---|---|
| S03, D05 | `lab-control#9` commit `0a28b2f3` |
| S04, R03, T01, T03 | `lab-control#9` commit `7f241a8d` |
| P04 | `lab-control#9` commit `d8ad5ad9` |
| L04 | `lab-control#9` commits `51dcb45c`, `0bf9ee3f` |
| D03 | `lab-control#9` commits `25f78794`, `7113f926` |
| K06 | `lab-control#9` commit `8d055e49` |
| K03 | `python-lib#19` |
| K05 | `sandbox-workspace#8` |

The bounded execution instructions are [`local-agent-handoff-03.md`](local-agent-handoff-03.md). Previously passing phases must not be repeated unnecessarily.

## External blockers

These remain `BLOCKED` rather than silently substituted:

- P06: private branch rulesets/protections;
- T04: OpenTofu private ruleset phase;
- L05: immutable private release-tag ruleset.

The current GitHub plan returns HTTP 403 for these private repository operations. Production requires a plan with private rulesets or an explicitly accepted lower-fidelity branch-protection fallback documented as a deviation.

## Security and supply chain

The final implementation uses:

- immutable action SHAs;
- pinned Copier/OpenTofu/provider/tool versions for acceptance;
- digest-pinned Renovate image and dry-run progression;
- Renovate scripts disabled;
- one exact allowlisted `uv lock` post-upgrade command;
- selected-repository GitHub App tokens;
- no persistent PAT architecture;
- `persist-credentials:false` where checkout is used;
- secret values excluded from reports, artifacts and OpenTofu state;
- reviewable PRs and automerge false.

## Migration plan — not executed

1. Obtain private-ruleset capability or approve the documented fallback.
2. Create production Apps with the permission split in `permission-model.md`.
3. Publish automation/components/template repositories and immutable refs.
4. Import/model one representative repository in OpenTofu read-only first.
5. Add topics, local Renovate preset and thin callers through an ordinary PR to `dev`.
6. Establish a no-change Copier baseline.
7. Run Renovate allowlist extract/lookup/full, then one live pilot PR with automerge off.
8. Require a clean second OpenTofu plan and one complete component/template/package/workflow update cycle.
9. Promote manually `dev → main` after review.
10. Expand repository by repository; remove legacy lifecycle code only after the last consumer leaves it.

## Rollback

- component regression: revert one template gitlink;
- template regression: pin the previous immutable template tag and run a normal Copier PR;
- workflow regression: revert the caller's exact automation SHA;
- repository configuration regression: review and apply the reverted OpenTofu plan;
- release regression: publish a corrected next tag; never move/delete a published tag;
- migration regression: remove managed topic/local Renovate config while ordinary Git history remains intact.

## Final decision

The principal architectural objective succeeds: custom code is no longer required for template assembly/update, fleet registry/synchronization, repository API orchestration, routine dependency freshness, CI body distribution, release bookkeeping or generic quality/package wrappers.

**Final current status: CONDITIONAL GO.**

The only external architectural blocker is private ruleset availability. The corrected implementation defects must receive the narrowly scoped handoff-03 live evidence before `lab-control#9`, `python-lib#19` and `sandbox-workspace#8` can leave draft. Production remains untouched.
