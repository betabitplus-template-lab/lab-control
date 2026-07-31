# Implementation Plan Structure

## Overview

This file defines how the execution plan under `plan/internal-implementation/`
should be structured.

Most important rules:

- Keep `plan/README.md` and `plan/implementation-notes.md` aligned with the
  phased plan.
- Split the execution plan across several markdown files.
- Plan the work as a dependency graph, not a flat list.
- Use one coherent phase per concept slice, vertical slice, or complete
  feature.

## Execution Folder

- Keep `plan/README.md` and `plan/implementation-notes.md` aligned with the
  phased plan under `plan/internal-discovery/` and
  `plan/internal-implementation/`.
- Create `plan/internal-implementation/`.
- Split the implementation plan across several markdown files instead of one
  large document.
- The plan must be detailed, systematic, and checklist-driven.

## Recommended Plan Shape

- `00-roadmap.md`:
  overall implementation stages, dependencies between phases, risks,
  sequencing, blocker analysis, parallelizable branches, and the planned work
  graph.
- `01-skeleton-and-boundaries.md`:
  top-down skeleton creation for `_internal`, including package layout,
  placeholder seams, ownership boundaries, base interfaces, and `_internal/config`
  package shape when runtime config exists.
- One phase file per concept slice, vertical slice, or complete feature:
  each file should cover one deliverable that can be implemented, tested,
  reviewed, and accepted on its own.
- One final cleanup file such as `90-final-cleanup-and-cutover.md`:
  removal of placeholders, dead code, transitional comments, temporary
  re-exports, whitespace misses, and any incomplete implementation leftovers.

## Delivery Order

- Plan the feature sequence in advance as a dependency graph, not as a flat
  list.
- Identify blockers, prerequisite slices, and work that can be parallelized
  safely before implementation starts.
- Start from the top down and create the `_internal` skeleton first.
- The skeleton phase may use plugs or placeholders to make the whole module
  shape visible early.
- After the skeleton exists, deliver one complete concept slice or feature at a
  time.
- Each phase should end in a state that is coherent, testable, and acceptable
  on its own.
- Do not leave the project in a half-cutover state between phases.
