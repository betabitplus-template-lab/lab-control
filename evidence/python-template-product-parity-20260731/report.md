# Python template product parity lab

Frozen baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99` / `python-lib-standard`.

## Result

The candidate keeps the generated Python-library product and replaces only platform-owned wiring.
The committed render excludes `uv.lock`: Copier does not render it, while the experiment generates and validates it during bootstrap.

- baseline rendered files: **170**
- candidate rendered files: **163**
- byte-identical retained files: **131**
- retained product hooks: **41** of 45 baseline hooks
- executed checks: **32**, all passed: **True**
- browsable candidate snapshot: `evidence/python-template-product-parity-20260731/rendered-sample`

## Removed platform-owned files

- `.devcontainer/Dockerfile.ci`
- `.github/actions/setup-dev-env/action.yml`
- `.github/scripts/install-sync-validation-tools.sh`
- `.github/workflows/build-ci-image.yml`
- `.github/workflows/python-lib-ci-baseline.yml`
- `.github/workflows/python-lib-ci-e2e-slice.yml`
- `.github/workflows/python-lib-ci-package.yml`
- `.github/workflows/sync-starter-template.yml`

## Added product helper

- `scripts/reproduce_running_loop.py`

The helper preserves the existing active-event-loop workbench diagnostic without retaining the legacy tooling monolith.

## Removed platform-only hooks

- `check-branch-name`
- `no-push-to-main`
- `py-lib-check-legacy-support-cleanup`
- `py-lib-template-check`

## Changed files

- `.agents/skills/plan-internal-from-contract/references/protocol/01-architecture-baseline.md`
- `.agents/skills/plan-internal-from-contract/references/protocol/05-final-state-and-pass-criteria.md`
- `.agents/skills/python-library-rules/SKILL.md`
- `.agents/skills/python-library-rules/references/core/logging_pattern.md`
- `.agents/skills/python-library-rules/references/core/public_api_pattern.md`
- `.agents/skills/python-library-rules/references/verification/e2e_test_template.md`
- `.agents/skills/python-library-rules/references/verification/test_file_template.md`
- `.agents/skills/python-library-rules/references/verification/tests_routing_pattern.md`
- `.agents/skills/python-library-rules/references/verification/workbench_script_template.md`
- `.envrc`
- `.github/MAINTAINER_SETUP.md`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.pre-commit-config.yaml`
- `CONTRIBUTING.md`
- `README.md`
- `SETUP.md`
- `_copier_answers.yml`
- `docs/sample_lib/verification/public-boundary-and-errors.md`
- `pyproject.toml`
- `renovate.json5`
- `scripts/README.md`
- `scripts/env/doctor.sh`
- `scripts/env/project_config.sh`
- `scripts/env/secrets.sh`
- `src/sample_lib/_internal/config/state.py`
- `tests/README.md`
- `tests/__init__.py`
- `tests/sample_lib/e2e/__init__.py`
- `tests/sample_lib/e2e/public_boundary/test_public_config_pipeline.py`
- `workbench/__init__.py`

## Executed checks

- PASS — `uv lock`
- PASS — `uv sync locked`
- PASS — `ruff lint`
- PASS — `ruff format`
- PASS — `ty`
- PASS — `pyright`
- PASS — `import linter`
- PASS — `Ternforge policy`
- PASS — `cognitive complexity`
- PASS — `class attribute order`
- PASS — `radon cyclomatic complexity`
- PASS — `radon maintainability`
- PASS — `bandit`
- PASS — `interrogate`
- PASS — `deptry`
- PASS — `policy tests`
- PASS — `active event-loop workbench diagnostic`
- PASS — `runtime export`
- PASS — `runtime dependency audit`
- PASS — `build`
- PASS — `twine metadata`
- PASS — `wheel contents`
- PASS — `manifest`
- PASS — `artifact venv`
- PASS — `install sample_lib-0.1.0-py3-none-any.whl`
- PASS — `import sample_lib-0.1.0-py3-none-any.whl`
- PASS — `artifact venv`
- PASS — `install sample_lib-0.1.0.tar.gz`
- PASS — `import sample_lib-0.1.0.tar.gz`
- PASS — `pre-commit stage`
- PASS — `pre-push stage`
- PASS — `candidate remains clean`

## Boundary proven

- Product trees, documentation, tests, examples, workbench, devcontainer, editor settings, agent kit, quality/security configuration, and local hooks remain in the generated repository.
- Old template assembly, local reusable CI bodies, CI image, template-sync workflow, branch-flow hooks, and legacy wrapper commands are absent.
- Runtime, policy, and test support use the already validated split packages; generic checks call standard tools directly.
