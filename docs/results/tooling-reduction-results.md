# Tooling reduction results

## Result

`py-lib-tooling` is 6,774 production LOC. Template/update and generic quality/package behavior can be removed. Two policy commands collapse into one 191-LOC stdlib checker; one running-loop utility is deferred as optional developer tooling.

## Quality wrappers

| Existing command | Direct replacement | Equivalence detail |
|---|---|---|
| `py-lib-check-radon-cc` | `radon cc -s -n <grade> <paths>` plus stdout-empty assertion | preserves legacy behavior that treats reported blocks as failure even where radon exits zero |
| `py-lib-check-radon-mi` | `radon mi -s -n <grade> <paths>` plus stdout-empty assertion | same threshold/report semantics |
| `py-lib-check-cognitive-complexity` | `flake8 --select CCR001 --max-cognitive-complexity=…` | plugin already supplies diagnostic |
| `py-lib-check-class-attributes-order` | `flake8 --select CCE001` | plugin direct invocation |
| `py-lib-audit-runtime-dependencies` | `uv export --frozen --no-dev … | pip-audit --no-deps --disable-pip -r -` | lock-frozen and avoids pip resolving a second graph |

Ruff, Pyright and import-linter are invoked directly. Wrappers are not retained merely to preserve historical command names.

## Packaging smoke

The three smoke commands are replaced by one ordinary CI chain:

```text
uv sync --frozen
uv build
twine check dist/*
check-wheel-contents dist/*.whl
check-manifest
install wheel in isolated uv venv
install sdist in separate isolated uv venv
import public package
run console script --help when present
pytest
```

This checks wheel/sdist contents, metadata, public import, console entry point and installed artifact execution without a custom artifact model.

## Template commands

| Existing command | Replacement |
|---|---|
| `py-lib-template-answer` | ordinary `.copier-answers.yml` |
| `py-lib-template-check` | Copier CLI/pretend, Renovate PR and CI |
| `py-lib-template-update` | Renovate Copier manager |
| `py-lib-refresh-shared-lock` | `uv lock` as an exact allowlisted post-upgrade task |

Copier tasks are not used for lock refresh because they expand the trusted executable-template boundary. Renovate scripts are disabled globally; only `^uv lock$` is allowed.

## Project information

`py-lib-project-info` is convenience aggregation and is replaced by:

- `uv version`;
- `uv tree`;
- a Python `tomllib` one-liner;
- standard package metadata;
- native GitHub contexts in Actions.

## Architecture policy

Generic imports are delegated to import-linter, Ruff private/tidy-import rules and Pyright. The residual checker handles only:

- console script targets `<primary>._api.cli:*` and the function exists;
- root `__init__.py` statement allowlist;
- literal string-based dynamic private imports;
- first line `# %%` for Python examples;
- required package/test/docs skeleton.

The prototype has no external dependency, runtime configuration, Copier wrapper, GitHub API, registry, updater or release code. Six focused unit tests pass.

## Running-loop helper

`py-lib-reproduce-running-loop` is not template lifecycle. Do not let it keep the package alive. Options, in order:

1. use IPython/pytest directly;
2. preserve a tiny standalone script in a developer-extras repository only if active users require it;
3. delete it if no downstream invocation is found.

This remains `DEFER`, not a platform dependency.

## Runtime package

`py-lib-runtime` stays separate. Its logging/cache/config helpers may overlap `structlog`, `diskcache`, `platformdirs`, `tenacity` and stdlib logging, but migration cost and public API compatibility must be evaluated as a normal library roadmap. Renovate should update its independent package version rather than template-sync logic.
