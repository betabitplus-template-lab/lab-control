# Tooling reduction results

## Result

`py-lib-tooling` is 6,774 production LOC. Generic template/update, quality and packaging behavior can be removed. Two unique policy commands collapse into one 196-LOC stdlib checker; one running-loop helper remains an optional developer utility.

Accepted evidence:

- direct quality parity: **8/8**;
- residual policy parity: **12/12**;
- exact generated-baseline policy: **PASS**;
- direct wheel/sdist metadata/install/import/pytest chain: **PASS**;
- legacy-answer Copier update with real lock change: **PASS** in handoff-04.

## Direct replacements

| Existing command | Replacement |
|---|---|
| `py-lib-check-radon-cc` | direct `radon cc` plus output assertion |
| `py-lib-check-radon-mi` | direct `radon mi` plus output assertion |
| `py-lib-check-cognitive-complexity` | direct flake8 plugin invocation |
| `py-lib-check-class-attributes-order` | direct flake8 plugin invocation |
| `py-lib-audit-runtime-dependencies` | frozen `uv export` then `pip-audit --no-deps --disable-pip` |
| `py-lib-template-answer` | `.copier-answers.yml` |
| `py-lib-template-check` | Copier/Renovate PR plus CI |
| `py-lib-template-update` | Renovate Copier manager |
| `py-lib-refresh-shared-lock` | exact allowlisted `uv lock` post-upgrade task |

The obsolete generated `py-lib-template-check` pre-push hook was removed in the `v0.4.3` template line. `sandbox-process#10` proves one atomic update containing answers, generated configuration, dependency metadata and `uv.lock` with green CI.

## Packaging smoke

The custom package-smoke commands are replaced by an ordinary CI chain:

```text
uv sync --frozen --all-groups
uv build
pinned twine check
pinned check-wheel-contents
check-manifest
isolated wheel install
isolated sdist install
public import / console help
pytest
```

No custom artifact model or package inspector remains necessary.

## PEP 508 Git dependencies

Two literal regex managers separately identify runtime and tooling while both use the shared source package `betabitplus/py-lib-starter`.

Handoff-04 established the exact remaining configuration defect:

- the literal `v` must remain outside `currentValue` so replacement preserves valid `@vX.Y.Z` syntax;
- grouping must match `depName` aliases, not the common `packageName`;
- both updates must be present before branch creation because the current source publishes one root tag stream.

The corrected preset uses:

```text
currentValue = numeric version only
matchDepNames = [py-lib-runtime, py-lib-tooling]
minimumGroupSize = 2
groupSlug = shared-python-git-packages
postUpgradeTasks = uv lock
```

A Node regression test passes locally and verifies extraction, replacement, re-extraction and grouping configuration. The reviewable publication is `automation#1@1554ac4295daa4c75d983ddab0fca1442b33e675`. One live K06 rerun remains.

## Residual policy

Generic import and type rules stay with import-linter, Ruff and Pyright. The retained checker handles only organization-specific console-script routing, root facade shape, literal private dynamic imports, runnable-example cell markers and required package/test/docs skeleton.

## Runtime package

`py-lib-runtime` remains an ordinary 2,133-LOC product library. It is outside the platform-lifecycle denominator. While runtime and tooling share one root tag stream, Renovate must update their refs atomically; independent package publication can be reconsidered separately.
