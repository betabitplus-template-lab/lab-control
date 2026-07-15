# Tooling reduction results

## Result

`py-lib-tooling` is 6,774 production LOC. Template/update and generic quality/package behavior can be removed. Two policy commands collapse into one 196-LOC stdlib checker; one running-loop utility is deferred as optional developer tooling.

Handoff-02 provided live evidence rather than static equivalence only:

- legacy/direct quality wrapper parity: **8/8**;
- residual policy rule parity on good/bad fixtures: **12/12**;
- wheel and sdist build, metadata and isolated install smoke: **PASS**;
- the first prepared all-in-one direct workflow exposed three self-containment defects, all corrected in `lab-control#9`.

## Quality wrappers

| Existing command | Direct replacement | Equivalence detail |
|---|---|---|
| `py-lib-check-radon-cc` | `radon cc -s -n <grade> <paths>` plus stdout-empty assertion | preserves legacy behavior that treats reported blocks as failure even where radon exits zero |
| `py-lib-check-radon-mi` | `radon mi -s -n <grade> <paths>` plus stdout-empty assertion | same threshold/report semantics |
| `py-lib-check-cognitive-complexity` | `flake8 --select CCR001 --max-cognitive-complexity=…` | plugin already supplies diagnostic |
| `py-lib-check-class-attributes-order` | `flake8 --select CCE001` | plugin direct invocation |
| `py-lib-audit-runtime-dependencies` | `uv export --frozen --no-dev …` then `pip-audit --no-deps --disable-pip` | lock-frozen and avoids pip resolving a second graph |

Ruff, Pyright and import-linter are invoked directly. Wrappers are not retained merely to preserve historical command names.

## Packaging smoke

The three smoke commands are replaced by one ordinary CI chain:

```text
uv sync --frozen --all-groups
uv build
uvx --from twine==6.2.0 twine check dist/*
uvx --from check-wheel-contents==0.6.3 check-wheel-contents dist/*.whl
uv run check-manifest --ignore .copier-answers.yml
install wheel in isolated uv venv
install sdist in separate isolated uv venv
import public package
run console script --help when present
pytest
```

Handoff-02 proved the underlying wheel/sdist path and found that the first workflow incorrectly assumed `twine` and `check-wheel-contents` were project dependencies and that check-manifest did not ignore the actual dotted Copier answers filename. The corrected workflow uses pinned ephemeral tools and the exact filename. Handoff-03 must run this exact prepared chain before D05 becomes PASS.

## Template and dependency commands

| Existing command | Replacement |
|---|---|
| `py-lib-template-answer` | ordinary `.copier-answers.yml` |
| `py-lib-template-check` | Copier CLI/pretend, Renovate PR and CI |
| `py-lib-template-update` | Renovate Copier manager |
| `py-lib-refresh-shared-lock` | `uv lock` as an exact allowlisted post-upgrade task |

Copier tasks are not used for lock refresh because they expand the trusted executable-template boundary. Renovate scripts are disabled globally; only exact `uv lock` is allowed.

Handoff-02 proved root and nested lock regeneration with private Git authentication and idempotency. It also exposed that Renovate's `pep621` manager does not extract the project's PEP 508 Git tag form. The downstream preset now adds a constrained regex manager only for:

```text
py-lib-runtime @ git+https://github.com/betabitplus/py-lib-starter.git@vX.Y.Z#subdirectory=packages/py-lib-runtime
py-lib-tooling @ git+https://github.com/betabitplus/py-lib-starter.git@vX.Y.Z#subdirectory=packages/py-lib-tooling
```

The datasource remains GitHub tags, versioning remains semver and `uv lock` remains the only post-upgrade command. Live extraction/update is assigned to handoff-03.

## Project information

`py-lib-project-info` is convenience aggregation and is replaced by `uv version`, `uv tree`, Python `tomllib`, standard package metadata and native GitHub Actions contexts.

## Architecture policy

Generic imports are delegated to import-linter, Ruff and Pyright. The residual checker handles only:

- console script targets `<primary>._api.cli:*` and the function exists;
- root `__init__.py` declaration/facade statement allowlist, including generated version fallback;
- literal string-based dynamic private imports;
- first line `# %%` for runnable Python examples, excluding package `__init__.py`;
- required package/test/docs skeleton.

The prototype has no external dependency, runtime configuration, Copier wrapper, GitHub API, registry, updater or release code. Eight focused tests pass locally. Handoff-03 must confirm it accepts the exact generated baseline that the legacy checker accepted.

## Running-loop helper

`py-lib-reproduce-running-loop` is not template lifecycle. Do not let it keep the package alive. Use IPython/pytest directly, preserve a tiny standalone developer utility only if active consumers require it, otherwise delete it. This remains `DEFER`, not a platform dependency.

## Runtime package

`py-lib-runtime` stays separate. Its logging/cache/config helpers may overlap `structlog`, `diskcache`, `platformdirs`, `tenacity` and stdlib logging, but migration cost and public API compatibility must be evaluated as a normal library roadmap. It is an ordinary versioned dependency, not template-sync logic.
