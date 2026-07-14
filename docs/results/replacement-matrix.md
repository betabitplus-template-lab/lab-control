# Replacement matrix

Baseline: `d59582375855cff69fb165e467dc5847bc75ca99`

The machine-readable file contains all 25 commands and 127 production modules. Prefixes below: `r/` = `src/py_lib_starter/`, `t/` = `packages/py-lib-tooling/src/py_lib_tooling/`, `p/` = `packages/py-lib-runtime/src/py_lib_runtime/`.

## Commands

| Command | Entry point | Implementation | LOC | Decision | Replacement |
|---|---|---|---:|---|---|
| py-lib-assemble-template | py_lib_starter._api.cli:assemble_template_main | r/_internal/template/components.py | 511 | DELETE | Copier template repositories + exact-SHA submodule |
| py-lib-check-platform-profile | py_lib_starter._api.cli:check_platform_profile_main | r/_internal/template/platform_profile.py | 496 | REPLACE | Copier render acceptance + filesystem checks |
| py-lib-check-starter-packages | py_lib_starter._api.cli:check_starter_packages_main | r/_internal/starter_packages_policy/check.py | 724 | REPLACE | Independent package/template CI |
| py-lib-check-template-components | py_lib_starter._api.cli:check_template_components_main | r/_internal/template/components.py | 511 | DELETE | gitlink review + generic symlink/render checks |
| py-lib-create-managed-repository | py_lib_starter._api.cli:create_managed_repository_main | r/_internal/managed_repository_onboarding/command.py | 108 | REPLACE | OpenTofu + Copier + thin bootstrap |
| py-lib-platform-health-report | py_lib_starter._api.cli:platform_health_report_main | r/_internal/downstream_registry/health.py | 172 | DELETE | Renovate dashboard + GitHub checks + OpenTofu plan |
| py-lib-platform-registry | py_lib_starter._api.cli:platform_registry_main | r/_internal/downstream_registry/cli.py | 174 | DELETE | GitHub topics + .copier-answers.yml |
| py-lib-audit-runtime-dependencies | py_lib_tooling._api.cli:audit_runtime_dependencies_main | t/_internal/quality_gates/commands.py | 267 | REPLACE | uv export --frozen --no-dev \| pip-audit -r - |
| py-lib-check-class-attributes-order | py_lib_tooling._api.cli:check_class_attributes_order_main | t/_internal/quality_gates/commands.py | 267 | REPLACE | flake8 --select CCE001 (plugin configured) |
| py-lib-check-cognitive-complexity | py_lib_tooling._api.cli:check_cognitive_complexity_main | t/_internal/quality_gates/commands.py | 267 | REPLACE | flake8 --select CCR001 --max-cognitive-complexity=… |
| py-lib-check-legacy-support-cleanup | py_lib_tooling._api.cli:check_legacy_support_cleanup_main | t/_internal/legacy_support_cleanup/command.py | 0 | DELETE | One-time migration checklist |
| py-lib-check-project-docs-structure | py_lib_tooling._api.cli:check_project_docs_structure_main | t/_internal/project_structure_policy/docs.py | 149 | RETAIN_MINIMAL | py-lib-policy docs skeleton rule |
| py-lib-check-project-structure | py_lib_tooling._api.cli:check_project_structure_main | t/_internal/project_structure_policy/project.py | 436 | RETAIN_MINIMAL | import-linter/Ruff/Pyright + py-lib-policy |
| py-lib-check-public-contract-boundary | py_lib_tooling._api.cli:check_public_contract_boundary_main | t/_internal/project_structure_policy/test_policy.py | 0 | REPLACE | import-linter + Ruff private/tidy imports + Pyright |
| py-lib-check-radon-cc | py_lib_tooling._api.cli:check_radon_cc_main | t/_internal/quality_gates/commands.py | 267 | REPLACE | radon cc -s -n <grade> <paths> |
| py-lib-check-radon-mi | py_lib_tooling._api.cli:check_radon_mi_main | t/_internal/quality_gates/commands.py | 267 | REPLACE | radon mi -s -n <grade> <paths> |
| py-lib-project-info | py_lib_tooling._api.cli:project_info_main | t/_internal/project_info/command.py | 0 | REPLACE | uv version; uv tree; Python tomllib; GitHub contexts |
| py-lib-refresh-shared-lock | py_lib_tooling._api.cli:refresh_shared_lock_main | t/_internal/template/lock.py | 93 | REPLACE | uv lock via allowlisted Renovate post-upgrade task |
| py-lib-reproduce-running-loop | py_lib_tooling._api.cli:reproduce_running_loop_main | t/_internal/diagnostics/running_loop.py | 0 | DEFER | IPython/pytest or separate optional dev utility |
| py-lib-smoke-built-artifacts | py_lib_tooling._api.cli:smoke_built_artifacts_main | t/_internal/smoke/built_artifacts.py | 266 | REPLACE | uv build + twine check + check-wheel-contents + check-manifest |
| py-lib-smoke-installed-artifact | py_lib_tooling._api.cli:smoke_installed_artifact_main | t/_internal/smoke/installed_artifact.py | 51 | REPLACE | isolated uv venv/install + pytest/import/console smoke |
| py-lib-smoke-public-api | py_lib_tooling._api.cli:smoke_public_api_main | t/_internal/smoke/public_api.py | 35 | REPLACE | pytest public import tests + import-linter |
| py-lib-template-answer | py_lib_tooling._api.cli:template_answer_main | t/_internal/template/answers.py | 146 | DELETE | standard .copier-answers.yml + Copier CLI |
| py-lib-template-check | py_lib_tooling._api.cli:template_check_main | t/_internal/template/check.py | 0 | DELETE | Renovate PR/dashboard + copier update --pretend |
| py-lib-template-update | py_lib_tooling._api.cli:template_update_main | t/_internal/template/update.py | 703 | DELETE | Renovate Copier manager |

## Complete module decisions

| Module | LOC | Decision |
|---|---:|---|
| `r/__init__.py` | 33 | DELETE |
| `r/_api/__init__.py` | 4 | DELETE |
| `r/_api/cli.py` | 32 | DELETE |
| `r/_api/config.py` | 11 | DELETE |
| `r/_api/defaults.py` | 10 | DELETE |
| `r/_api/errors.py` | 18 | DELETE |
| `r/_api/platform.py` | 18 | DELETE |
| `r/_api/types.py` | 14 | DELETE |
| `r/_internal/__init__.py` | 38 | DELETE |
| `r/_internal/config/__init__.py` | 20 | DELETE |
| `r/_internal/config/assembly.py` | 17 | DELETE |
| `r/_internal/config/models.py` | 17 | DELETE |
| `r/_internal/config/state.py` | 45 | DELETE |
| `r/_internal/config/validation.py` | 14 | DELETE |
| `r/_internal/downstream_registry/__init__.py` | 1 | DELETE |
| `r/_internal/downstream_registry/cli.py` | 174 | DELETE |
| `r/_internal/downstream_registry/discovery.py` | 56 | DELETE |
| `r/_internal/downstream_registry/health.py` | 172 | DELETE |
| `r/_internal/downstream_registry/operations.py` | 83 | DELETE |
| `r/_internal/downstream_registry/output.py` | 78 | DELETE |
| `r/_internal/downstream_registry/parser.py` | 71 | DELETE |
| `r/_internal/downstream_registry/registry.py` | 206 | DELETE |
| `r/_internal/managed_repository_onboarding/__init__.py` | 57 | REPLACE |
| `r/_internal/managed_repository_onboarding/cli.py` | 163 | REPLACE |
| `r/_internal/managed_repository_onboarding/command.py` | 108 | REPLACE |
| `r/_internal/managed_repository_onboarding/model.py` | 218 | REPLACE |
| `r/_internal/managed_repository_onboarding/preflight.py` | 101 | REPLACE |
| `r/_internal/managed_repository_onboarding/setup_local.py` | 310 | REPLACE |
| `r/_internal/managed_repository_onboarding/setup_platform.py` | 258 | REPLACE |
| `r/_internal/managed_repository_onboarding/state_discovery.py` | 193 | REPLACE |
| `r/_internal/managed_repository_onboarding/template_refs.py` | 66 | REPLACE |
| `r/_internal/managed_repository_onboarding/validation_completion.py` | 109 | REPLACE |
| `r/_internal/managed_repository_onboarding/validation_workflows.py` | 244 | REPLACE |
| `r/_internal/starter_packages_policy/__init__.py` | 2 | REPLACE |
| `r/_internal/starter_packages_policy/check.py` | 724 | REPLACE |
| `r/_internal/template/__init__.py` | 0 | DELETE |
| `r/_internal/template/components.py` | 511 | DELETE |
| `r/_internal/template/platform_profile.py` | 496 | DELETE |
| `t/__init__.py` | 138 | DELETE |
| `t/_api/__init__.py` | 11 | DELETE |
| `t/_api/cli.py` | 80 | DELETE |
| `t/_api/config.py` | 11 | DELETE |
| `t/_api/defaults.py` | 9 | DELETE |
| `t/_api/errors.py` | 8 | DELETE |
| `t/_api/project_info.py` | 22 | DELETE |
| `t/_api/project_structure.py` | 17 | DELETE |
| `t/_api/template.py` | 53 | DELETE |
| `t/_api/test_support.py` | 191 | DELETE |
| `t/_api/types.py` | 16 | DELETE |
| `t/_internal/__init__.py` | 153 | DELETE |
| `t/_internal/config/__init__.py` | 16 | DELETE |
| `t/_internal/config/assembly.py` | 45 | DELETE |
| `t/_internal/config/models.py` | 90 | DELETE |
| `t/_internal/config/state.py` | 40 | DELETE |
| `t/_internal/config/validation.py` | 81 | DELETE |
| `t/_internal/diagnostics/__init__.py` | 2 | DEFER |
| `t/_internal/diagnostics/reproduce_running_loop.py` | 57 | DEFER |
| `t/_internal/legacy_support_cleanup/__init__.py` | 2 | DELETE |
| `t/_internal/legacy_support_cleanup/leftovers.py` | 256 | DELETE |
| `t/_internal/project_info/__init__.py` | 8 | REPLACE |
| `t/_internal/project_info/service.py` | 91 | REPLACE |
| `t/_internal/project_structure_policy/__init__.py` | 0 | REPLACE |
| `t/_internal/project_structure_policy/api.py` | 192 | REPLACE |
| `t/_internal/project_structure_policy/api_declarations.py` | 202 | REPLACE |
| `t/_internal/project_structure_policy/api_imports.py` | 66 | REPLACE |
| `t/_internal/project_structure_policy/common.py` | 39 | RETAIN_MINIMAL |
| `t/_internal/project_structure_policy/docs.py` | 149 | RETAIN_MINIMAL |
| `t/_internal/project_structure_policy/examples.py` | 183 | RETAIN_MINIMAL |
| `t/_internal/project_structure_policy/project.py` | 436 | RETAIN_MINIMAL |
| `t/_internal/project_structure_policy/public_contract.py` | 130 | REPLACE |
| `t/_internal/project_structure_policy/root_entrypoint.py` | 131 | RETAIN_MINIMAL |
| `t/_internal/project_structure_policy/tests.py` | 137 | REPLACE |
| `t/_internal/project_structure_policy/workbench.py` | 30 | RETAIN_MINIMAL |
| `t/_internal/quality_gates/__init__.py` | 0 | REPLACE |
| `t/_internal/quality_gates/change_title.py` | 90 | REPLACE |
| `t/_internal/quality_gates/commands.py` | 267 | REPLACE |
| `t/_internal/smoke/__init__.py` | 2 | REPLACE |
| `t/_internal/smoke/built_artifacts.py` | 266 | REPLACE |
| `t/_internal/smoke/installed_artifact.py` | 51 | REPLACE |
| `t/_internal/smoke/public_api.py` | 35 | REPLACE |
| `t/_internal/template/__init__.py` | 2 | REPLACE |
| `t/_internal/template/answers.py` | 146 | REPLACE |
| `t/_internal/template/hygiene.py` | 111 | REPLACE |
| `t/_internal/template/lock.py` | 93 | REPLACE |
| `t/_internal/template/mixed_policy.py` | 151 | REPLACE |
| `t/_internal/template/ownership.py` | 89 | REPLACE |
| `t/_internal/template/pyproject_edit.py` | 235 | REPLACE |
| `t/_internal/template/pyproject_format.py` | 34 | REPLACE |
| `t/_internal/template/shared_package_refs.py` | 256 | REPLACE |
| `t/_internal/template/trusted_update.py` | 104 | REPLACE |
| `t/_internal/template/update.py` | 703 | REPLACE |
| `t/_internal/template/update_policy.py` | 57 | REPLACE |
| `t/_internal/test_support/__init__.py` | 51 | DEFER |
| `t/_internal/test_support/_console_appearance.py` | 85 | DEFER |
| `t/_internal/test_support/_vcr_shared.py` | 329 | DEFER |
| `t/_internal/test_support/console.py` | 261 | DEFER |
| `t/_internal/test_support/e2e_vcr_guard.py` | 61 | DEFER |
| `t/_internal/test_support/images.py` | 26 | DEFER |
| `t/_internal/test_support/paths.py` | 53 | DEFER |
| `t/_internal/test_support/setup.py` | 82 | DEFER |
| `t/_internal/test_support/vcr_matchers.py` | 42 | DEFER |
| `p/__init__.py` | 97 | PRODUCT_LIBRARY |
| `p/_api/__init__.py` | 12 | PRODUCT_LIBRARY |
| `p/_api/cache.py` | 86 | PRODUCT_LIBRARY |
| `p/_api/config.py` | 14 | PRODUCT_LIBRARY |
| `p/_api/defaults.py` | 20 | PRODUCT_LIBRARY |
| `p/_api/errors.py` | 18 | PRODUCT_LIBRARY |
| `p/_api/logging.py` | 123 | PRODUCT_LIBRARY |
| `p/_api/previews.py` | 39 | PRODUCT_LIBRARY |
| `p/_api/types.py` | 54 | PRODUCT_LIBRARY |
| `p/_api/validation.py` | 20 | PRODUCT_LIBRARY |
| `p/_internal/__init__.py` | 47 | PRODUCT_LIBRARY |
| `p/_internal/cache/__init__.py` | 11 | PRODUCT_LIBRARY |
| `p/_internal/cache/base.py` | 434 | PRODUCT_LIBRARY |
| `p/_internal/cache/decorators.py` | 236 | PRODUCT_LIBRARY |
| `p/_internal/cache/paths.py` | 27 | PRODUCT_LIBRARY |
| `p/_internal/config/__init__.py` | 27 | PRODUCT_LIBRARY |
| `p/_internal/config/assembly.py` | 26 | PRODUCT_LIBRARY |
| `p/_internal/config/models.py` | 171 | PRODUCT_LIBRARY |
| `p/_internal/config/state.py` | 30 | PRODUCT_LIBRARY |
| `p/_internal/config/validation.py` | 116 | PRODUCT_LIBRARY |
| `p/_internal/logging/__init__.py` | 19 | PRODUCT_LIBRARY |
| `p/_internal/logging/service.py` | 362 | PRODUCT_LIBRARY |
| `p/_internal/previews/__init__.py` | 11 | PRODUCT_LIBRARY |
| `p/_internal/previews/formatting.py` | 88 | PRODUCT_LIBRARY |
| `p/_internal/validation/__init__.py` | 11 | PRODUCT_LIBRARY |
| `p/_internal/validation/numbers.py` | 34 | PRODUCT_LIBRARY |

## Totals

| Decision | Commands | Modules |
|---|---:|---:|
| DELETE | 8 | 44 |
| REPLACE | 14 | 40 |
| RETAIN_MINIMAL | 2 → one checker | 6 |
| PRODUCT_LIBRARY | 0 | 26 |
| DEFER | 1 | 11 |

Decision rationale and exact residual responsibilities are documented in `minimal-custom-surface.md`, `tooling-reduction-results.md`, and ADR 0003.
