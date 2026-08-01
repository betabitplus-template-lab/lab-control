# Contributing

Start with [SETUP.md](SETUP.md) to provision the local environment. If your
local environment feels off, run `bash scripts/env/doctor.sh` before debugging
deeper.

Use [docs/sample_lib/README.md](docs/sample_lib/README.md) for package
docs, [tests/README.md](tests/README.md) for test-tree layout, and
[docs/sample_lib/verification/README.md](docs/sample_lib/verification/README.md)
for verification guidance.

Repository-wide package and reusable-zone checks read metadata from
`[tool.ternforge]` in `pyproject.toml`. When repo-local scripts or shared
test support need package names or env-var prefixes, use
`py_lib_testkit.get_project_tooling_config` instead of hardcoding them.

`py-lib-runtime` is consumed as a runtime dependency and `py-lib-testkit` is
consumed as a dev dependency from the shared py starter repository through
one shared version tag. Keep this repo thin: import shared runtime helpers, call
shared console commands, and import shared test helpers instead of copying
reusable implementation files locally.

## Branch And Target Flow

- Normal development lands on `dev`.
- Direct pushes to `main` are blocked by a pre-push hook.
- Branch names must match the enforced local convention: `feature/`, `fix/`,
  `chore/`, `hotfix/`, `release/`, `codex/`, or the long-lived `dev` / `main`
  branches.

## Local Validation

Run commit-time hooks:

```bash
uv run pre-commit run --all-files
```

Run push-time hooks:

```bash
uv run pre-commit run --all-files --hook-stage pre-push
```

## Template And Tooling Updates

Check whether this repo is behind the released Ternforge template:

```bash
uvx --from copier==9.17.0 copier check-update
```

Apply the latest released Ternforge template:

```bash
uvx --from copier==9.17.0 copier update
```

The update command leaves product-owned `src/`, `tests/`, `docs/`,
`examples/`, and `workbench/` files alone by default. Review the resulting
diff, run validation, then land the update through the normal pull request to `main`.

## Running Tests

Run the package test suite:

```bash
uv run pytest tests/sample_lib
```

Run only hermetic tests:

```bash
uv run pytest tests/sample_lib -m hermetic
```

Run all tests:

```bash
uv run pytest
```

## Running Tests Directly

If you run test files directly, ensure the repo root is on `PYTHONPATH`.
The tracked `.envrc` configures this automatically for direnv-aware shells.

## Runnable Examples

`examples/` is for committed public API demonstrations. Add an example when a
complete caller flow is clearer as a real Python file than as a short docs
snippet.

Run an example directly:

```bash
direnv exec . uv run python examples/sample_lib/<module>.py
```

Keep examples focused on imports from `sample_lib`. If an example
needs private modules, move that investigation to `workbench/` or convert it
into a test.

Every committed example should have a matching link from the package usage docs.
The e2e examples smoke test discovers and runs committed example scripts so
docs examples do not drift silently.

## Live Workbench Scripts

`workbench/` is manual-only. Add focused probes there when a behavior needs
live investigation outside committed pytest coverage.

Run a probe directly:

```bash
direnv exec . uv run python -m workbench.sample_lib.<module>
```

Reproduce the same probe inside an already-running event loop:

```bash
direnv exec . uv run python scripts/reproduce_running_loop.py \
    workbench.sample_lib.<module>
```

## Commit And Release Conventions

This project uses [Commitizen](https://commitizen-tools.github.io/commitizen/)
for version management and changelog generation. Commit messages and pull
request titles must follow [Conventional Commits](https://www.conventionalcommits.org/)
format, for example `feat: add retry policy`, `fix(cache): preserve metadata`,
or `chore(ci): update workflows`. Use GitHub's draft state instead of a `WIP`
title prefix.

For every pull request to `main`, choose the title according to
the highest release impact it contains: breaking change first, then `feat`,
then `fix`, otherwise an appropriate non-release type such as `docs` or
`chore`. CI validates the format, while the maintainer remains responsible for
choosing the correct semantic type.

Full CI runs on every pull request targeting `main`. Merges to `main` run the release workflow.
