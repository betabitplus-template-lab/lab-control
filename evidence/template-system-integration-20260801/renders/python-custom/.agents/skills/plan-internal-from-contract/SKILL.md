---
name: plan-internal-from-contract
description: Create a detailed implementation plan for a private `_internal` package from the live repository contract around it. Use when Codex needs to plan a fresh, replacement, or first-time `_internal` implementation in a Python project that already has a top-level public package, `_api`, optional package-specific `_support`, docs, workbench, and tests that define the boundary and behavior to preserve, while avoiding git history and producing checklist-driven discovery and execution plans under `plan/`.
---

# Plan `_internal` From Contract

## Overview

Create a planning package for implementing `<package_name>._internal` from the
current repository state.

Stay in planning mode. Discover the live contract first, define the target
private architecture second, and write an execution-ready phased plan without
implementing `_internal` unless the user explicitly asks for code changes.

## Non-Optional Completion Rules

- Read the full split protocol before writing or revising plan files.
- `references/protocol/05-final-state-and-pass-criteria.md` defines the exact
  pass criteria and success criteria for the future implementing agent.
- `references/planning-protocol.md` is compatibility-only. The canonical first
  read is `references/protocol/README.md`.

## Protocol Read Order

Read these files in order before writing plan files:

1. `references/protocol/README.md`
2. `references/protocol/01-architecture-baseline.md`
3. `references/protocol/02-discovery-stage.md`
4. `references/protocol/03-implementation-plan-structure.md`
5. `references/protocol/04-phase-rules.md`
6. `references/protocol/05-final-state-and-pass-criteria.md`
7. `references/protocol/06-implementation-boundaries.md`

Do not stop after reading only one protocol file. The protocol is intentionally
split so required rules do not get lost in one large document.

## Workflow

1. Resolve the target repo and confirm it exposes the expected contract
   surfaces. Substitute the discovered package name everywhere this skill uses
   `<package_name>`:
   - `src/<package_name>/__init__.py` or the repo-relative equivalent package
     root
   - `src/<package_name>/_api/`
   - `src/<package_name>/_support/` only if present
   - `docs/<package_name>/architecture/`
   - `workbench/`
   - `tests/<package_name>/`
2. Read `references/protocol/README.md` before writing plan files, then read
   the full split protocol in the order it prescribes.
3. Treat the current tree as the only source of truth. Do not inspect git
   history or prior implementations.
4. Inspect `_api`, package-specific `_support` if present, architecture docs,
   workbench, e2e tests, and property-based public-contract tests before
   prescribing a target shape.
5. Create `plan/README.md` as the root execution task for the future
   implementing agent. Use
   `references/plan_root_readme_template.md`, and include the exact
   no-git-history instruction it requires.
6. Create `plan/implementation-notes.md` as active working memory for the
   implementing agent. Use
   `references/implementation_notes_template.md`.
7. Create `plan/internal-discovery/` and write every required discovery file.
8. Create `plan/internal-implementation/` and split the execution plan across
   small checklist-driven phase files.
9. Use `references/implementation_phase_template.md` for ordinary concept-slice
   or feature-slice phase files.
10. Keep the plan concrete. Name real files, module seams, tests, docs, and
    logging or exception responsibilities instead of brainstorming.
11. Bias toward more detail when choosing between two acceptable plan shapes.
    Name expected modules, classes, functions, dataclasses, protocols, import
    seams, and preserved public symbols whenever they are inferable from the
    live tree.
12. Preserve the public contract and implementation boundaries exactly as the
   protocol requires.

## Output

- `plan/README.md`
- `plan/implementation-notes.md`
- `plan/internal-discovery/01-workbench-live-probes.md`
- `plan/internal-discovery/02-public-contract.md`
- `plan/internal-discovery/03-preserved-functionality.md`
- `plan/internal-discovery/04-target-internal-architecture.md`
- `plan/internal-discovery/05-internal-docs-coverage.md`
- `plan/internal-discovery/06-internal-logging-coverage.md`
- `plan/internal-discovery/07-internal-exception-plan.md`
- `plan/internal-discovery/08-principles.md`
- `plan/internal-implementation/00-roadmap.md`
- `plan/internal-implementation/01-skeleton-and-boundaries.md`
- one implementation phase file per concept slice, vertical slice, or complete
  feature
- `plan/internal-implementation/90-final-cleanup-and-cutover.md`

## Constraints

- Stay in planning mode unless the user explicitly requests implementation.
- Use only the live repo tree as input.
- Do not inspect git history.
- Treat current docs, tests, `_api`, present package-specific `_support`, and
  workbench as the contract.
- Mirror the architecture concept slices when they improve structure and
  navigation.
- Keep outputs concrete, implementation-useful, and checklist-driven.
- Surface missing contract inputs or repository mismatches before writing
  speculative phases.

## Reference Map

- `references/protocol/README.md`
  Read first.
  Explains the split protocol, the read order, and the minimum required read
  set.
- `references/protocol/01-architecture-baseline.md`
  Read for the architecture and engineering baseline.
- `references/protocol/02-discovery-stage.md`
  Read for the discovery-stage rules, required discovery files, and
  discovery-note expectations.
- `references/protocol/03-implementation-plan-structure.md`
  Read for the execution-folder rules, recommended plan shape, and delivery
  order.
- `references/protocol/04-phase-rules.md`
  Read for phase checklist rules, template usage, and testing/docs rules per
  phase.
- `references/protocol/05-final-state-and-pass-criteria.md`
  Read for final-state requirements and the exact pass criteria and success
  criteria.
- `references/protocol/06-implementation-boundaries.md`
  Read for the strict allowed-edit paths and implementation boundaries.
- `references/planning-protocol.md`
  Compatibility index for the split protocol files.
  Use it only when a prior instruction still points at the old path.
- `references/plan_root_readme_template.md`
  Read when creating `plan/README.md` for the future implementing agent.
- `references/implementation_notes_template.md`
  Read when creating `plan/implementation-notes.md`.
- `references/implementation_phase_template.md`
  Read when creating ordinary phase files under
  `plan/internal-implementation/`.
