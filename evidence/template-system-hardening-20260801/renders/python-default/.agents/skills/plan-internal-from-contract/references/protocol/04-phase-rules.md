# Phase Rules

## Overview

This file defines how each implementation phase should be written.

Most important rules:

- Every stage and phase must be checklist-driven.
- Every phase must state prerequisites, dependents, safe parallel work, and a
  verification gate.
- Prefer exact files, exact seams, and exact rerun commands.
- Keep tests under the approved test roots and docs under the implementation
  docs root.

## Phase Rules

- Every stage and phase must be written as a checklist so progress is easy to
  track.
- Every phase should state its prerequisites, follow-up dependents, and any
  safe parallel work.
- Every phase must define intermediate verification criteria before work
  starts.
- A phase may proceed only when its verification criteria are satisfied.
- Prefer file-by-file and seam-by-seam detail over umbrella statements. When a
  phase can predict concrete modules, symbols, invariants, or translation
  boundaries, name them explicitly.
- Add links back to discovery files only where the current phase item is
  explicitly driven by that contract, regression proof, ownership rule, log
  plan, exception boundary, or doc requirement.
- Prefer exact direct commands for phase-local proof. When a hook or check is
  only practical repo-wide, say that explicitly and give the exact repo-wide
  command.
- Prefer concept-centric or feature-centric folder and file names for
  implementation docs and tests.
- Do not collect many unrelated behaviors into one large test file or one large
  phase file.

## Phase Template

Use `references/implementation_phase_template.md`.

Adapt it only when a phase genuinely needs a different structure.

## Testing And Documentation Rules Per Phase

- After each phase is implemented, cover it with unit tests and integration
  tests.
- Use `references/implementation_phase_template.md` for the exact test and docs
  roots, naming and alignment rules, file-by-file planning expectations, and
  phase-local rerun command expectations.
