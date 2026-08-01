# Downstream CI, local DX, and direct execution

Outcome: **FAILED**

## Migrated consumer results

| Consumer | Functional CI | Runtime audit | Local DX | Direct execution |
|---|---:|---:|---:|---:|
| `llm-router` | FLAKY (1 initial failure; 13 reruns passed) | FAIL (frozen dependency vulnerabilities) | FAIL | NOT RUN (external layers disabled) |
| `reddit-scraper` | PASS | FAIL (frozen dependency vulnerabilities) | FAIL | PUBLIC E2E PASS; LIVE WORKBENCH 403 |
| `visual-annotation` | PASS | FAIL (frozen dependency vulnerabilities) | FAIL | PASS |
| `web-tools` | PASS | FAIL (frozen dependency vulnerabilities) | FAIL | PASS |

Functional CI excludes the separately reported vulnerability audit. The one initial llm-router randomized/parallel failure passed 10/10 targeted reruns and 3/3 full-suite reruns, so it is classified as a timing flake rather than a deterministic migration regression.

## Local-DX and migration findings

* **DX-IMMUTABLE-HADOLINT (blocking)** — FAIL: new devcontainer Dockerfile uses hadolint releases/latest. pin hadolint release and verify checksum or use a pinned devcontainer feature/image.
* **DX-IMMUTABLE-UV-INSTALLER (blocking)** — FAIL: new devcontainer Dockerfile executes an unversioned remote uv installer. use a pinned uv image/digest or a versioned installer with integrity verification.
* **DX-DEVCONTAINER-BASE-IMAGE (blocking)** — FAIL: the devcontainer base image is selected by a mutable Python-series tag without an image digest. pin the selected devcontainer image by digest and let Renovate review updates.
* **DX-MACOS-BASH-PORTABILITY (blocking)** — FAIL: project_config.sh and secrets.sh require Bash mapfile and fail under the macOS system Bash used by the documented commands. remove project_config.sh and implement any retained secret-file loop with Bash-3-compatible constructs.
* **DX-SYSTEM-PYTHON-TOMLLIB (blocking)** — FAIL: secrets.sh reads TOML with arbitrary system python3 and fails when that interpreter predates tomllib. use the already-selected project interpreter or avoid Python/TOML parsing in the shell path.
* **DX-SETUP-LOCKED (blocking)** — FAIL: setup.sh runs uv sync without --locked and can silently rewrite dependency state during contributor bootstrap. use uv sync --locked --all-groups (or the exact required groups) and fail on lock drift.
* **DX-HOST-HOOK-BOOTSTRAP (blocking)** — FAIL: generated hooks require host hadolint and shellcheck, but setup.sh installs neither and doctor.sh checks neither. use pinned pre-commit-managed hooks where practical or make pinned prerequisites explicit in setup and doctor.
* **DX-CONDITIONAL-SOPS-PREREQUISITE (blocking)** — FAIL: repositories with declared encrypted env files require sops, but the generic doctor does not validate that conditional prerequisite. keep secret loading optional and check sops only when [tool.ternforge.secrets].env_files is non-empty.
* **DX-DEVCONTAINER-DOCTOR-PARITY (blocking)** — FAIL: the built devcontainer lacks direnv while doctor.sh treats direnv as a mandatory command. make direnv a host-only requirement or install it in the devcontainer; doctor must understand the active environment.
* **DX-COPIER-ANSWERS-CUTOVER (blocking)** — FAIL: the new template owns .copier-answers.yml while all frozen consumers use _copier_answers.yml and the EXP-0036 migration updates but does not rename the old file. rename the answers file atomically during migration and verify copier check-update against the released template.
* **DX-DEAD-PROJECT-CONFIG-SHELL (simplification)** — FAIL: project_config.sh exports PY_LIB_PROJECT_ENV_PREFIX, but the generated product has no consumer for that value. delete project_config.sh and its .envrc/doctor wiring; testkit can read [tool.ternforge] directly.
* **DX-ENVRC-NARROWNESS (simplification)** — FAIL: .envrc performs unused project-config parsing before its useful venv/PYTHONPATH/optional-secret responsibilities. reduce .envrc to venv activation, PYTHONPATH, and an explicit optional secret loader.
* **DX-SCRIPTS-README-DUPLICATE (minor)** — FAIL: scripts README repeats the same policy command twice. keep one policy command and list distinct artifact/structure commands only.

## Direct execution interpretation

* `visual-annotation`: e2e and workbench pass under `python -m`, IPython `%run -m`, and the active-event-loop wrapper. Removing `# %%` from either an e2e or workbench module is rejected by policy, and restoring it returns the repository to green.
* `web-tools`: live e2e and workbench pass under all three execution modes.
* `reddit-scraper`: the public e2e module passes under all three modes. The direct live workbench is externally unstable: one IPython run succeeded while normal Python and active-loop runs received Reddit HTTP 403 without the optional proxy secret.
* `llm-router`: live direct execution was intentionally excluded because its external intermediate layers are disabled; its full hermetic test suite was still included in CI validation.

## Devcontainer

* Dockerfile build: PASS.
* The post-create sync was attempted but exhausted the available Docker storage while downloading the large dev group, so that run is environmental/incomplete rather than a product verdict.
* Independent image inspection shows `git`, `uv`, `shellcheck`, and `hadolint` present, but `direnv`, `gh`, and `sops` absent. `gh` is optional; the mandatory direnv check contradicts the image contents, and sops must be conditional on declared secret files.

## Failed commands

* `llm-router` / `ci` / `ci-llm-router-pytest-ci-shape` → `logs/ci-llm-router-pytest-ci-shape.log`
* `llm-router` / `ci` / `ci-llm-router-runtime-audit` → `logs/ci-llm-router-runtime-audit.log`
* `llm-router` / `dx` / `dx-llm-router-doctor` → `logs/dx-llm-router-doctor.log`
* `llm-router` / `dx` / `dx-llm-router-project-config` → `logs/dx-llm-router-project-config.log`
* `llm-router` / `dx` / `dx-llm-router-copier-check-update` → `logs/dx-llm-router-copier-check-update.log`
* `reddit-scraper` / `ci` / `ci-reddit-scraper-runtime-audit` → `logs/ci-reddit-scraper-runtime-audit.log`
* `reddit-scraper` / `dx` / `dx-reddit-scraper-doctor` → `logs/dx-reddit-scraper-doctor.log`
* `reddit-scraper` / `dx` / `dx-reddit-scraper-project-config` → `logs/dx-reddit-scraper-project-config.log`
* `reddit-scraper` / `dx` / `dx-reddit-scraper-copier-check-update` → `logs/dx-reddit-scraper-copier-check-update.log`
* `reddit-scraper` / `direct_execution` / `e2e-reddit-scraper-workbench-python-module` → `logs/e2e-reddit-scraper-workbench-python-module.log`
* `reddit-scraper` / `direct_execution` / `e2e-reddit-scraper-workbench-active-loop` → `logs/e2e-reddit-scraper-workbench-active-loop.log`
* `visual-annotation` / `ci` / `ci-visual-annotation-runtime-audit` → `logs/ci-visual-annotation-runtime-audit.log`
* `visual-annotation` / `dx` / `dx-visual-annotation-doctor` → `logs/dx-visual-annotation-doctor.log`
* `visual-annotation` / `dx` / `dx-visual-annotation-project-config` → `logs/dx-visual-annotation-project-config.log`
* `visual-annotation` / `dx` / `dx-visual-annotation-empty-secrets-noop` → `logs/dx-visual-annotation-empty-secrets-noop.log`
* `visual-annotation` / `dx` / `dx-visual-annotation-copier-check-update` → `logs/dx-visual-annotation-copier-check-update.log`
* `web-tools` / `ci` / `ci-web-tools-runtime-audit` → `logs/ci-web-tools-runtime-audit.log`
* `web-tools` / `dx` / `dx-web-tools-doctor` → `logs/dx-web-tools-doctor.log`
* `web-tools` / `dx` / `dx-web-tools-project-config` → `logs/dx-web-tools-project-config.log`
* `web-tools` / `dx` / `dx-web-tools-empty-secrets-noop` → `logs/dx-web-tools-empty-secrets-noop.log`
* `web-tools` / `dx` / `dx-web-tools-copier-check-update` → `logs/dx-web-tools-copier-check-update.log`
* `web-tools` / `dx` / `dx-web-tools-pre-push-stage` → `logs/dx-web-tools-pre-push-stage.log`
* `devcontainer` / `post_create_and_doctor` → `logs/dx-web-tools-devcontainer-post-create-and-doctor.log`

## Interpretation

The migrated Python product and direct runnable/testkit behavior are largely intact, but the local contributor surface and Copier provenance are not migration-ready. Runtime success does not override reproducibility or portability failures: working unpinned downloads, Linux-only shell code, and an unusable answers-file cutover remain blocking defects.
