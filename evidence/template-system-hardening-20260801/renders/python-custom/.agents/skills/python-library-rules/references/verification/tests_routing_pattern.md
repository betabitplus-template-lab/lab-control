---
name: tests-routing-pattern
description: Reusable test-tree routing patterns for Python projects. Use when you need consistent placement rules for helpers, support modules, and end-to-end tests under tests/.
---

# Tests Routing

## Overview

Use this guide for reusable test-tree routing patterns.

## When To Use

Use this guide when deciding where new package-specific helpers, support
modules, or e2e files should live under `tests/`.

Use this guide when the test tree needs a stable routing rule instead of
project-specific placement guesses.

If the package docs already use `architecture/concepts/` as the primary
vertical-slice taxonomy, use the same grouping under `tests/<project>/e2e/`
when the scenarios prove those same slices.

If the project uses property-based testing for both public-contract invariants
and private implementation invariants, keep those as explicit sibling groups
under `tests/<project>/property_based/` instead of mixing them in one flat
package.

## Core Patterns

### Tree Pattern

Use this layout for the whole `tests/` tree:

- `tests/support/`
  Legacy cross-project test infrastructure. In Ternforge-managed Python libraries,
  prefer top-level `py_lib_testkit` helpers instead of creating or mirroring
  this folder.
- `tests/<project>/support/`
  Project-specific helpers for one package or service
- `tests/<project>/e2e/`
  End-to-end scenario groups
- `tests/<project>/e2e/<group>/`
  Scenario scripts for one testing group
- `tests/<project>/e2e/<group>/cassettes/`
  Replay artifacts for that testing group when replay-backed tests exist

### Routing Pattern

Use these placement rules:

- import generic setup, replay, console, path, and image helpers from the
  supported top-level `py_lib_testkit` package
- put builders, assertions, fixture-specific helpers, and integration checks in
  `tests/<project>/support/`
- keep `tests/<project>/e2e/` focused on scenario groups, not shared helpers
- when architecture concept docs define the stable slice grouping, mirror that
  grouping in `tests/<project>/e2e/` instead of inventing separate proof buckets
- keep `tests/<project>/property_based/public_contract/` for generated checks
  that protect only the supported package surface
- keep `tests/<project>/property_based/internal/` for generated checks that
  intentionally target private implementation invariants
- test public config behavior through the top-level package, including
  install/read behavior and `TypeError` for non-config install inputs
- when one public-contract property file cleanly protects one architecture
  concept slice, mirror that concept in the filename
- keep each e2e group folder focused on scenarios, not project-wide helpers

### Import Pattern

Use these import rules:

- import shared support directly from top-level `py_lib_testkit` in
  Ternforge-managed Python libraries
- import project support directly from `tests.<project>.support...`
- keep `tests/<project>/e2e/`, `tests/<project>/support/`, and
  `tests/<project>/property_based/public_contract/` on the supported public
  package boundary
- allow `tests/<project>/unit/`, `tests/<project>/integration/`, and
  `tests/<project>/property_based/internal/` to import private modules
  directly when those files intentionally verify private implementation seams
- use package-level setup in `tests.<project>.e2e` instead of local group
  setup modules
- do not add other local redirection modules in e2e group folders
