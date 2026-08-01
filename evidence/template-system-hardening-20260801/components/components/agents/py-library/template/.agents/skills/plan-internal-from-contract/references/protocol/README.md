# Planning Protocol Map

## Overview

Read this file first. The planning protocol is intentionally split across
focused files so important requirements do not get buried in one large
document.

Most important rules:

- Use only the current repo tree as input.
- Do not inspect git history or prior implementations.
- Preserve the current public contract and implementation boundaries.
- Read the focused protocol files below in order before writing plan files.

## Read Order

1. `references/protocol/01-architecture-baseline.md`
2. `references/protocol/02-discovery-stage.md`
3. `references/protocol/03-implementation-plan-structure.md`
4. `references/protocol/04-phase-rules.md`
5. `references/protocol/05-final-state-and-pass-criteria.md`
6. `references/protocol/06-implementation-boundaries.md`

## Minimum Required Read Set

Read every file in the order above before writing or revising a planning
package for `_internal`.

The files are short on purpose. Do not stop after reading only one of them.

## File Map

- `01-architecture-baseline.md`
  Project shape, `_internal` architecture rules, style, logging, and
  exceptions.
- `02-discovery-stage.md`
  Discovery folder rules, root plan files, required discovery files, and
  discovery-note rules.
- `03-implementation-plan-structure.md`
  Execution-folder rules, recommended plan shape, and delivery order.
- `04-phase-rules.md`
  Phase checklist rules, template usage, and testing/docs rules per phase.
- `05-final-state-and-pass-criteria.md`
  Final-state requirements and the exact pass criteria and success criteria the
  finished implementation must meet.
- `06-implementation-boundaries.md`
  Exact allowed edit paths and the strict contract-following rules for the
  future implementing agent.

## Compatibility Note

`references/planning-protocol.md` still exists as a compatibility index. It now
points here instead of carrying the full protocol in one mega file.
