# ADR 0003: Replace py-lib-tooling policy surface with direct tools and minimal checker

- Status: Proposed — implementation prototype accepted
- Date: 2026-07-15

## Context

`py-lib-tooling` combines generic quality/package/template operations, test fixtures, diagnostics and organization-specific architecture conventions. Retaining the package merely to preserve command names would keep thousands of lines and an artificial platform dependency.

## Decision

1. Delete template answer/check/update and lock orchestration APIs; invoke Copier, Renovate and uv directly.
2. Invoke radon, flake8 plugins, pip-audit, Ruff, Pyright, import-linter, pytest and packaging tools directly.
3. Replace custom package smoke with build/check/isolated-install CI.
4. Collapse `py-lib-check-project-structure` and `py-lib-check-project-docs-structure` into one stdlib-only `py-lib-policy` CLI/pre-commit hook.
5. Limit the checker to conventions not adequately covered by generic tools:
   - console scripts through `_api.cli`;
   - declaration-only root `__init__.py`;
   - literal dynamic imports of `_internal`;
   - `# %%` examples;
   - required source/test/docs skeleton.
6. Keep no runtime config, Copier wrapper, GitHub client, registry, updater, release logic or product helper in the checker.
7. Treat the running-loop helper separately as optional developer utility; it cannot justify retaining `py-lib-tooling`.
8. Keep `py-lib-runtime` independent from this decision.

## Prototype evidence

- 191 substantive LOC;
- Python standard library only;
- one CLI entry point;
- six focused tests passing;
- deterministic file/line diagnostics;
- suitable for pre-commit and CI.

## Consequences

- generic tool behavior and upgrades are no longer reimplemented;
- configuration becomes visible in standard tool files/workflows;
- historical command names are intentionally broken during migration and require release notes;
- unique policy remains owned and testable;
- optional developer utilities must move or be deleted independently.

## Follow-up

Run the old checker, direct tools and residual checker against the frozen good/bad fixtures in handoff 02. Any lost meaningful diagnostic must either be expressed in standard configuration or added as a small focused rule; it must not reintroduce the old framework.
