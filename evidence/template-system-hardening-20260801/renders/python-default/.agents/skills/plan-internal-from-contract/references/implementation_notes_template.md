---
name: implementation-notes-template
description: Template for `plan/implementation-notes.md`. Use when creating the active working-notes file for the future implementing agent.
---

# Implementation Notes Template

## Overview

Use this template for `plan/implementation-notes.md`.

## When To Use

Use this template when the planning package needs one short file where a future
implementing agent can keep active notes during execution.

## File Shape

1. title
2. `Overview`
3. `Current Focus`
4. `Open Questions`
5. `Blockers Or Cautions`
6. `Recent Verification`
7. `Failed Or Rejected Approaches`
8. `Next Actions`

## Rules

- Keep the file short, current, and disposable.
- Use it for working memory, not durable architecture prose.
- Tell the implementing agent to review it at session start, before changing
  phases, after major verification runs, and before stopping work.
- Encourage short notes about blockers, rejected approaches, recent command
  outcomes, and next actions.
- Tell the implementing agent to keep the notes current during the phase and
  refresh them immediately on phase completion or before any pause.
- Encourage removing or rewriting stale notes once they stop being useful.

## Template

```md
# Implementation Notes

## Overview

This file is working memory for the agent implementing the plan.

Review it at session start, before changing phases, after major verification
runs, and before stopping work. Keep it short, current, and concrete. See
[README.md](README.md) for the task rules.

## Current Focus

- Active phase:
- Active files:
- Immediate goal:

## Open Questions

- None recorded.

## Blockers Or Cautions

- None recorded.

## Recent Verification

- None recorded.

## Failed Or Rejected Approaches

- None recorded.

## Next Actions

- Read the current phase file and the notes above before making more changes.
- Update the relevant plan checklists only when work and verification are
  truly complete.
- Keep this file current during the phase and refresh it on phase completion or
  before any pause.
```
