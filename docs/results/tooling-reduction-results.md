# Tooling reduction results

## Result

`py-lib-tooling` is 6,774 production LOC. Template/update and generic quality/package behavior can be removed. Two policy commands collapse into one 196-LOC stdlib checker; one running-loop utility is deferred as optional developer tooling.

Live evidence now includes:

- legacy/direct quality wrapper parity: **8/8**;
- residual policy fixture parity: **12/12**;
- exact generated-baseline policy parity: **PASS**;
- direct wheel/sdist build, metadata, isolated installs and pytest: **PASS**;
- wheel SHA-256 `d0a4f11f563aeded804fd86ecf82e576f3d1589b454b62055a55223c35553041`;
- sdist SHA-256 `b88e32fd2068ec8aab65fe9f07a21cc4bfb2c00aeb00ac160369a3ab01933fcc`.

## Quality wrappers

| Existing command | Direct replacement | Equivalence detail |
|---|---|---|
| `py-lib-check-radon-cc` | `radon cc -s -n <grade> <paths>` plus stdout-empty assertion | preserves legacy failure-on-reported-block behavior |
| `py-lib-check-radon-mi` | `radon mi -s -n <grade> <paths>` plus stdout-empty assertion | preserves the historical threshold/report behavior |
| `py-lib-check-cognitive-complexity` | `flake8 --select CCR001 --max-cognitive-complexity=…` | plugin supplies the diagnostic directly |
| `py-lib-check-class-attributes-order` | `flake8 --select CCE001` | plugin direct invocation |
| `py-lib-audit-runtime-dependencies` | frozen `uv export` then `pip-audit --no-deps --disable-pip` | audits the lock graph without a second resolver |

Ruff, Pyright and import-linter are invoked directly. Historical wrapper command names are not retained.

## Packaging smoke

The three custom smoke commands are replaced by one ordinary chain:

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

Handoff-03 executed this exact path successfully. No custom artifact model or package inspector remains necessary.

## Template and dependency commands

| Existing command | Replacement |
|---|---|
| `py-lib-template-answer` | ordinary `.copier-answers.yml` |
| `py-lib-template-check` | Copier CLI, Renovate PR and CI |
| `py-lib-template-update` | Renovate Copier manager |
| `py-lib-refresh-shared-lock` | exact allowlisted `uv lock` post-upgrade task |

The obsolete generated pre-push invocation of `py-lib-template-check` is now explicitly removed by `experiments/remediation/k03-components.patch`. The target no longer carries a compatibility hook that assumes `_copier_answers.yml`.

## PEP 508 Git dependencies

Two literal Renovate regex managers separately extract:

```text
py-lib-runtime @ git+https://github.com/betabitplus/py-lib-starter.git@vX.Y.Z#subdirectory=packages/py-lib-runtime
py-lib-tooling @ git+https://github.com/betabitplus/py-lib-starter.git@vX.Y.Z#subdirectory=packages/py-lib-tooling
```

Handoff-03 proved the dry extraction/lookup shape but found a live `depName mismatch` and an invalid mixed-ref lock fixture. The corrected preset:

- uses one literal manager per dependency;
- sets explicit `depNameTemplate` and `packageNameTemplate`;
- keeps GitHub tags and semver extraction;
- groups both updates into one PR because the current packages share one root repository tag;
- keeps exact `uv lock` as the only post-upgrade command.

Final live grouped-PR/idempotency evidence is K06 in handoff-04.

## Architecture policy

Generic imports are delegated to import-linter, Ruff and Pyright. The residual checker handles only:

- console script routing through `<primary>._api.cli:*`;
- root `__init__.py` declaration/facade shape;
- literal dynamic private imports;
- `# %%` for runnable example files;
- required package/test/docs skeleton.

The dependency-free checker and preserved legacy behavior both accepted the exact generated baseline `sandbox-process@d594c0dd80908f89bc5a534681f27765fb985c4b`.

## Running-loop helper

`py-lib-reproduce-running-loop` is not template lifecycle. Use IPython/pytest directly, retain a tiny standalone developer utility only if active consumers require it, otherwise delete it. This remains `DEFER`.

## Runtime package

`py-lib-runtime` remains an ordinary 2,133-LOC product library. It is not template-sync logic. Runtime and tooling are separately detectable dependencies, but while both are published from one root tag their Renovate ref change must remain grouped to preserve a valid lock.
