# ADR 0003: Replace py-lib-tooling policy surface with direct tools and minimal checker

- Status: Accepted for target design — migration not started
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
   - declaration/facade-only root `__init__.py`, including the generated version fallback;
   - literal dynamic imports of `_internal`;
   - `# %%` runnable examples, excluding package `__init__.py` files;
   - required source/test/docs skeleton.
6. Keep no runtime config, Copier wrapper, GitHub client, registry, updater, release logic or product helper in the checker.
7. Treat the running-loop helper separately as optional developer utility; it cannot justify retaining `py-lib-tooling`.
8. Keep `py-lib-runtime` independent from this decision.
9. Remove the obsolete generated `py-lib-template-check` pre-push hook; Copier update freshness belongs to Renovate/CI rather than a legacy wrapper expecting `_copier_answers.yml`.

## Evidence

- 196 substantive LOC;
- Python standard library only;
- one CLI entry point;
- eight focused unit tests passing;
- legacy/direct generic-rule parity: 8/8;
- residual policy fixture parity: 12/12;
- corrected checker and preserved legacy checker both accept `sandbox-process@d594c0dd80908f89bc5a534681f27765fb985c4b`;
- deterministic file/line diagnostics;
- direct wheel/sdist packaging and isolated-install chain passed.

## Consequences

- generic tool behavior and upgrades are no longer reimplemented;
- configuration becomes visible in standard tool files/workflows;
- historical command names intentionally disappear during migration and require release notes;
- unique policy remains owned, small and testable;
- optional developer utilities must move or be deleted independently;
- accepting this ADR does not authorize production deletion until consumers migrate through reviewed PRs.

## Follow-up

Complete K03/K06 live update delivery in handoff-04, then migrate consumer repositories incrementally. Any later lost meaningful diagnostic must be expressed in standard configuration or a small focused rule; it must not reintroduce the old framework.
