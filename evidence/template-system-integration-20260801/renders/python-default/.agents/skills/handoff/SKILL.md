---
name: handoff
description: Write a strong HANDOFF.md for the current project state. Use when Codex needs to capture progress for the next agent, including what was tried, what worked, what failed, current blockers, and the best next steps. Default target is the current workspace, but a path can be provided.
---

# Handoff

## Overview

Use this skill to leave the next agent a clean starting point.

## Workflow

1. Resolve the target first. Use the current workspace by default unless the
   user gives a path.
2. Inspect the current repo state, recent work, changed files, docs, and any
   relevant logs or outputs.
3. Write `HANDOFF.md` in the target root.
4. Capture the real current state, not a plan written from memory.
5. Explain what was tried, what worked, what did not, what is still blocked,
   and what the next agent should do first.
6. Include enough concrete detail that a fresh agent can continue from just
   `HANDOFF.md`.

## Handoff Shape

Keep the file concise but complete. Cover:

- what the project or task is
- what changed
- what was tried
- what worked
- what did not work
- current blockers or open questions
- the best next steps
- important files, commands, branches, or paths if they matter

## Constraints

- Prefer concrete facts over guesses.
- Preserve important context that is easy to lose across sessions.
- Do not pad the file with generic summaries if nothing happened.
- If the target already has a `HANDOFF.md`, update it deliberately instead of
  blindly appending noise.
