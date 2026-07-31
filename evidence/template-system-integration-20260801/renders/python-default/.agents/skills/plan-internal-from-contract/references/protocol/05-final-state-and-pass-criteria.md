# Final State And Pass Criteria

## Overview

This file defines what "done" means for the future implementing agent.
It is the canonical source for the completion success criteria and pass
criteria.

Most important rules:

- The end state must be clean, final, and production-ready.
- No placeholders, legacy leftovers, or half-finished seams may remain.
- The implementation is not complete until the exact success criteria and pass
  criteria below are satisfied.

## Pass Criteria

- All `pytest` suites pass.
- All pre-commit and pre-push hooks pass.
- `lint-imports` passes after any package-boundary or config-lifecycle change.
- All project rules and architectural requirements are satisfied.
- Every relevant e2e or workbench script successfully runs in module mode and,
  for Ternforge-managed Python libraries, via
  `uv run python scripts/reproduce_running_loop.py <module>` when already-running-loop
  behavior matters.

## Final State Rules

- The end state must be clean, final, and production-ready.
- No backward-compatibility shims, legacy paths, dead code, transitional
  comments, or temporary re-exports should remain.
- No plugs, placeholders, whitespace misses, or half-finished seams should be
  left at the end.
- If config management is in scope, `_api/defaults.py` is declarative,
  `_api/config.py` is thin, config mechanics live under `_internal/config/`,
  and install-time cache invalidation is covered by explicit import-linter
  rules and public behavior tests.
