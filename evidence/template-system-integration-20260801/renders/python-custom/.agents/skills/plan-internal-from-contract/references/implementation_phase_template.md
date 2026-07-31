---
name: implementation-phase-template
description: Template for ordinary `plan/internal-implementation/*.md` phase files. Use when creating a concept-slice or feature-slice execution phase.
---

# Implementation Phase Template

## Overview

Use this template for ordinary phase files under
`plan/internal-implementation/`.

## When To Use

Use this template when creating a concept-slice or feature-slice phase that
can be implemented, tested, and accepted on its own.

Do not use it for `00-roadmap.md` or `90-final-cleanup-and-cutover.md` when
those files need a different shape.

## File Shape

1. title
2. `Goal`
3. `Scope`
4. `Implementation Checklist`
5. `Tests`
6. `Implementation Docs`
7. `Verification Gate`

## Rules

- Keep the phase narrow enough to be coherent and reviewable on its own.
- State prerequisites, follow-up dependents, safe parallel work, and
  verification gates before the implementation checklist.
- Name exact `_internal`, test, and docs files whenever they are predictable.
- Prefer narrow verification commands for the phase-local proof.
- If a hook or quality check is only practical repo-wide, say that explicitly
  and give the exact repo-wide command.
- Place tests only under
  `tests/<package_name>/unit/`,
  `tests/<package_name>/integration/`, and
  `tests/<package_name>/property_based/internal/`.
- Place implementation docs only under `docs/<package_name>/implementation/`.
- For both tests and docs, prefer one root-level file when the slice is
  coherent in one file; otherwise use a semantically named folder and keep the
  files narrow.
- Use the same vertical-slice, concept, or feature vocabulary across docs and
  tests, and keep names aligned when they cover the same slice.
- When an existing public-contract or e2e proof depends on a later phase, name
  it and mark it as later proof rather than the immediate gate.
- Add inline links back to discovery docs only when a current item is directly
  driven by that discovery fact, proof, or boundary rule.

## Template

```md
# Phase: <Concept Or Feature Name>

## Goal

- [ ] Define the exact outcome of this phase.
- [ ] Name the concrete deliverables this phase finishes: modules, symbols,
  seams, or behaviors.

## Scope

- [ ] List `_internal` modules and files to create or update.
- [ ] If this phase touches config, list the exact `_internal/config` files and
  public root exports affected.
- [ ] List helper files needed for low-level details.
- [ ] List the expected classes, functions, dataclasses, protocols, or
  re-exports this phase should introduce or finalize when they are predictable.
- [ ] List public-contract assumptions that must remain unchanged.
- [ ] List relevant `workbench` probes when they exist and explain how they can help development or validation for this slice.
- [ ] List prerequisites, follow-up dependents, blockers, and safe parallel
  work for this phase.

## Implementation Checklist

- [ ] Create or refine the skeleton for this slice.
- [ ] Implement core orchestration.
- [ ] Move parsing, formatting, and protocol details into helper files.
- [ ] Keep config mechanics inside `_internal/config` when this phase touches
  defaults, config snapshots, install state, or cache invalidation.
- [ ] Use relevant `workbench` probes during development when this slice has them.
- [ ] Add docstrings, inline comments, and section banners where needed.
- [ ] Add logging coverage.
- [ ] Add exception coverage and boundary normalization.

## Tests

- [ ] List exact unit test files to create or update. State what each file proves and the narrow command to run that file or folder.
- [ ] List exact integration test files to create or update. State what each file proves and the narrow command to run that file or folder.
- [ ] List exact internal property-based files when this slice has invariants. State what each file proves and the narrow command to run that file or folder.
- [ ] Name the key invariants, public error shapes, trace fields, or logging
  events each planned test file protects when that is predictable.
- [ ] For config phases, include public-root tests for install/read behavior,
  non-config `TypeError`, and cache invalidation when runtime objects capture
  config snapshots.
- [ ] List existing public-contract or e2e proof files to keep green.
- [ ] Mark any existing proof that depends on a later phase as later proof, not the immediate blocking gate.

## Implementation Docs

- [ ] List exact docs to create or update.
- [ ] Keep the planned docs naming and folder organization aligned with the planned test files or folders for the same slice when practical.
- [ ] State briefly what each doc must contain: diagram, walkthrough, rules, and any slice-specific trade-offs.

## Verification Gate

- [ ] Exact phase-local test and validation commands pass.
- [ ] Relevant later public proofs are named when they are not yet unblocked.
- [ ] Relevant repo-wide hooks and quality checks are named explicitly when they cannot be narrowed safely.
- [ ] The slice is coherent and does not rely on placeholder behavior.
- [ ] Boundaries and names match the target concept slice or feature.
- [ ] Logging, exceptions, and docs are present where needed.
- [ ] The implementation doc includes the rules and architectural requirements followed.
```
