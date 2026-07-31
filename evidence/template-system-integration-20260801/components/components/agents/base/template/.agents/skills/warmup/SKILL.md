---
name: warmup
description: Research a codebase deeply before working in it. Use when Codex needs to inspect how a project works, read code and docs, build solid project knowledge first, or answer focused research questions about a local folder, another path, or a repo URL.
---

# Warmup

## Overview

Use this skill to learn a codebase before changing it.

## Inputs

- Default target: the current codebase.
- Optional target: a local path or repo URL.
- Optional hints: research questions, priority areas, or scope limits.

## Workflow

1. Resolve the target first. Use the current repo by default unless the user
   gives a path or URL.
2. If the target is local, inspect the tree directly. If it is a URL, inspect
   the repo through available tools or explain what access is still needed.
3. Read the high-level docs, setup docs, architecture docs, and entrypoints
   first to map the project shape.
4. Cover the codebase broadly after that: public API, internal structure,
   runtime flow, tests, scripts, and docs.
5. Use subagents to split the research across major areas when that helps cover
   the project faster and more completely.
6. Treat user hints as priority questions, but still build enough broad context
   to understand how the project fits together.
7. Do not return early after a shallow skim. Come back only once the project is
   well understood or a concrete access blocker is reached.

## Output

- Summarize what the project does, how it is organized, and how it runs.
- Call out the most important modules, docs, tests, and workflows.
- Answer the user's priority questions if they provided any.
- Name any blind spots or blocked areas explicitly.
