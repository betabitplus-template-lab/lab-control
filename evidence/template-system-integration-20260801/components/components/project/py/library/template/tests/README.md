# Tests Layout

The `tests/` tree is split into reusable tooling support and package-specific
tests.

## Reusable Support

`py_lib_testkit` exposes reusable testing infrastructure from its supported
public root.

Typical contents:

- direct-run setup
- console/rendering helpers for manual demos
- shared repo/test-data path helpers
- generic pytest-process setup

Reusable support may read repository metadata from `[tool.ternforge]`, but
it should not import the product package or assume its public APIs.

## Package-Specific Support

`tests/[[[ package_name ]]]/support/` contains helpers that are specific to this
package and reused by more than one test module.

Typical contents:

- package-specific builders
- package-specific assertions
- e2e validation helpers

Keep one-off scenario data inside the test file that proves it. Do not add a
shared scenario helper module just to avoid repeating a tiny example.

## Pytest Configuration

Root `tests/conftest.py` is intentionally reusable and should stay free of
product-package imports. Product-wide fixtures live in
`tests/<package>/conftest.py`.

## Test Layers

- `unit/` checks focused public and private seams.
- `integration/` checks package-level collaboration.
- `property_based/public_contract/` checks public invariants.
- `property_based/internal/` checks private implementation invariants.
- `e2e/` contains direct-runnable public behavior scenarios.

If the project adds external HTTP e2e tests, add replay support deliberately and
document the recording/update process next to that slice.
