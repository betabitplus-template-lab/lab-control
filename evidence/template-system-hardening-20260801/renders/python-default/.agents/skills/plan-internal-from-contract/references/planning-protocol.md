# Planning Protocol Index

## Overview

This file used to carry the full planning protocol. It is now a compatibility
index that points to the split protocol files under `references/protocol/`.

Read `references/protocol/README.md` first.

Most important rules:

- Use only the current repo tree as input.
- Do not inspect git history or prior implementations.
- Preserve the public contract and implementation boundaries exactly.
- Read every split protocol file in the documented order before writing plan
  files.

## Split Protocol Files

- `references/protocol/README.md`
  Read first. Explains the split, the required read order, and the minimum read
  set.
- `references/protocol/01-architecture-baseline.md`
  Architecture and engineering baseline.
- `references/protocol/02-discovery-stage.md`
  Discovery-stage rules, required discovery files, and discovery-note
  expectations.
- `references/protocol/03-implementation-plan-structure.md`
  Execution-folder rules, recommended plan shape, and delivery order.
- `references/protocol/04-phase-rules.md`
  Phase checklist rules, template usage, and testing/docs rules per phase.
- `references/protocol/05-final-state-and-pass-criteria.md`
  Final-state requirements and exact pass criteria and success criteria.
- `references/protocol/06-implementation-boundaries.md`
  Exact allowed edit paths and strict implementation boundaries.
