# Minimal custom surface

## Decision

The current root/tooling surface is 11,466 production LOC. The strict template/update lifecycle subset is 6,673 LOC. The target platform needs no reusable Python lifecycle package and no long-running service.

## Retained components

| Component | Substantive LOC | Dependencies | Exact responsibility | Why a ready-made tool is insufficient | Maintenance cost | Hook/CI form |
|---|---:|---|---|---|---|---|
| `experiments/minimal-policy/py_lib_policy.py` | 196 | Python stdlib | organization-specific `_api`/`_internal`, console-script, root-init, dynamic import, example and skeleton conventions | generic import tools do not express TOML entry-point targets, declaration-only AST shape, `# %%` first-line or required docs paths together | low; one AST/fs pass, eight focused tests | one CLI and pre-commit hook |
| `provisioning/bootstrap.sh` | 15 | tofu, copier, git | coordinate `tofu apply → copier copy → first dev push → tofu apply` | declarative provider cannot create the first project commit from a Copier render | low; no state machine or GitHub API | operator/CI script |
| `ensure-promotion-pr.yml` | 22 | GitHub Actions/CLI | create at most one `dev → main` PR when GitHub compare reports a diff | GitHub can merge/queue an existing PR but does not create this promotion PR automatically | low; stateless/idempotent; no checkout/fetch credentials | reusable workflow |
| `renovate/controller/run-phases.sh` | 11 | Docker | enforce image digest and extract→lookup→full order | Renovate accepts individual dry modes but does not enforce this organization rollout sequence itself | very low | controller script |
| `secure-workflow-update.yml` | 99 | GitHub Actions + dedicated App | replace one exact reusable-workflow SHA in one selected repository and open a PR | main Renovate intentionally lacks Workflows write; GitHub does not provide a declarative automatic ref bump | low/conditional; narrow validation and no merge | workflow dispatcher |
| `component-wiring/check-wiring.sh` | 12 | git/find/bash | reject broken links, conflict markers and diff whitespace | final-template output-path ownership is project policy, not a package-manager concern | very low | CI/pre-commit |

## Totals

- Mandatory lifecycle coordination without workflow updater: **48 LOC**.
- Preferred lifecycle surface including the separate updater: **147 LOC**.
- Generic wiring guard: **12 LOC**.
- Unique policy: **196 LOC**.
- Total direct executable custom non-product code: **355 LOC**.

For conservative planning, the final report retains an upper bound of 151 lifecycle LOC and 359 total LOC. Both figures are below 3.2% of the current 11,466 root/tooling source and below 2.3% of the 6,673 strict lifecycle subset for the lifecycle-only surface.

Declarative YAML/HCL/JSON is not counted as a custom application package. It still requires review, but it does not introduce a new API, runtime framework or state machine.

## Handoff-02 effect

Live execution did not reveal a need for any new lifecycle subsystem. Every failure was corrected inside the existing narrow components:

- promotion orchestration became smaller by removing checkout/fetch;
- private Copier authentication remained workflow configuration rather than a Python credential helper;
- PEP 508 Git extraction remained a Renovate regex manager rather than a custom dependency scanner;
- OpenTofu schema correction removed an unsupported field rather than adding provisioning code;
- policy false positives were corrected inside the existing stdlib checker.

## Explicitly absent

- template assembler;
- update engine;
- manifest inheritance/collision engine;
- downstream registry;
- fleet synchronizer;
- GitHub API adapters;
- release service;
- runtime configuration scaffold;
- quality command wrappers;
- custom package artifact inspector.

## `py-lib-runtime`

`py-lib-runtime` is 2,133 production LOC and remains outside these totals. It is an ordinary product library with logging/config/cache/previews APIs. It should be moved/versioned independently and updated as a normal dependency. Individual helpers may later be replaced by `structlog`, `platformdirs`, `diskcache`, `tenacity` or stdlib logging, but that is a product API migration decision, not template-platform orchestration.
