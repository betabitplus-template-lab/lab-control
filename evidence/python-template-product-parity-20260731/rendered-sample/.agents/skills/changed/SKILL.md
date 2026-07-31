---
name: changed
description: Reconcile with intentional local user changes before continuing. Use when the user signals that the workspace changed since Codex last worked and Codex should inspect the current repo state, refresh its assumptions, and preserve those changes instead of undoing or "fixing" them.
---

# Changed

## Overview

Use this skill to realign with the live workspace before continuing.

## Inputs

- Default target: the current workspace.
- Optional target: a local path.
- Optional hints: files, areas, or changes to inspect first.

## Workflow

1. Resolve the target first. Use the current workspace by default unless the
   user gives a path.
2. Inspect the live repo state first: changed files, current contents, and any
   relevant diffs.
3. Compare the current state to your recent assumptions, plans, or unfinished
   work if that context exists.
4. Treat user-kept changes as intentional unless the user explicitly says
   otherwise.
5. Update your plan around the current state instead of trying to restore an
   older version.
6. If a local change creates a real conflict with the new request, explain the
   conflict instead of silently rewriting it.
7. Summarize what changed, what it means, and how you will proceed.

## Constraints

- Do not revert, clean up, or "fix" local changes just because they differ
  from a prior plan.
- Prefer reading current files and diffs over reasoning from memory.
- Preserve user wording, structure, and code unless the user asks for a change.
- If the repo state is ambiguous, explain the ambiguity instead of guessing.
