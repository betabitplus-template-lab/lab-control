# Minimal custom surface

## Decision

The current root/tooling surface is 11,466 production LOC. The strict template/update lifecycle subset is 6,673 LOC. The target platform needs no reusable Python lifecycle package and no long-running service.

## Retained components

| Component | Substantive LOC | Dependencies | Exact responsibility | Why a ready-made tool is insufficient | Maintenance cost | Hook/CI form |
|---|---:|---|---|---|---|---|
| `experiments/minimal-policy/py_lib_policy.py` | 196 | Python stdlib | organization-specific `_api`/`_internal`, console-script, root-init, dynamic import, example and skeleton conventions | generic import tools do not express TOML entry-point targets, declaration-only AST shape, `# %%` first-line or required docs paths together | low; one AST/fs pass, eight focused tests | one CLI and pre-commit hook |
| `provisioning/bootstrap.sh` | 25 | tofu, copier, git | coordinate the first `dev` push and exit safely when the remote is already initialized | declarative provider cannot create the first project commit from a Copier render | low; one remote-ref guard, no state machine or GitHub API | operator/CI script |
| `ensure-promotion-pr.yml` | 26 | GitHub Actions/CLI | create at most one `dev → main` PR when GitHub compare reports a diff | GitHub can merge/queue an existing PR but does not create this promotion PR automatically | low; stateless/idempotent; no checkout/fetch credentials | reusable workflow |
| `renovate/controller/run-phases.sh` | 11 | Docker | enforce image digest and extract→lookup→full order | Renovate accepts individual dry modes but does not enforce this organization rollout sequence itself | very low | controller script |
| `secure-workflow-update.yml` | 103 | GitHub Actions + dedicated App | replace one exact reusable-workflow SHA in one selected repository and open a PR | main Renovate intentionally lacks Workflows write; GitHub does not provide a declarative automatic ref bump | low/conditional; narrow validation and no merge | workflow dispatcher |
| `component-wiring/check-wiring.sh` | 12 | git/find/bash | reject broken links, conflict markers and diff whitespace | final-template output-path ownership is project policy, not a package-manager concern | very low | CI/pre-commit |

## Totals

- Mandatory lifecycle coordination without workflow updater: **62 LOC**.
- Preferred lifecycle surface including the separate updater: **165 LOC**.
- Generic wiring guard: **12 LOC**.
- Unique policy: **196 LOC**.
- Total direct executable custom non-product code: **373 LOC**.

The lifecycle-only surface is still a **97.5% reduction** from the 6,673-LOC strict lifecycle subset. The complete executable non-product surface is a **96.7% reduction** from the current 11,466 root/tooling source.

Declarative YAML/HCL/JSON and hardened first-stage evidence workflows are reviewed configuration, not counted as a new application package or lifecycle service.

## Handoff-03 effect

Live execution still revealed no need for a new subsystem. The final corrections remain inside the narrow components already selected:

- repository-scoped GitHub CLI calls in the promotion workflow;
- one remote-ref idempotency guard in the bootstrap script;
- two literal Renovate regex managers, grouped because runtime/tooling share one root tag;
- removal of an obsolete legacy pre-push wrapper from the generated component;
- exact-SHA, selected-repository and ephemeral-auth hardening for inherited lab workflows.

## Explicitly absent

- template assembler;
- update engine;
- manifest inheritance/collision engine;
- downstream registry;
- fleet synchronizer;
- GitHub API adapter package;
- release service;
- runtime configuration scaffold;
- quality command wrappers;
- custom package artifact inspector.

## `py-lib-runtime`

`py-lib-runtime` is 2,133 production LOC and remains outside these totals. It is an ordinary product library with logging/config/cache/previews APIs. It should be moved/versioned independently and updated as a normal dependency. While runtime and tooling still share one production root tag, Renovate detects them separately but updates them as one grouped ref change so the lock cannot contain conflicting source revisions.
