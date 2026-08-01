# Agent Rules

## Python Library Rules Skill

- Use the repo-local `$python-library-rules` skill extensively as the default engineering baseline for Python development, planning, review, and refactor work.
- Read `.agents/skills/python-library-rules/SKILL.md` first.
- Start with `references/core/README.md`, then load the narrowest relevant files under `references/core/` before consulting narrower docs or verification references.
- Treat `references/core/` as the primary source for package boundaries, defaults, config, logging, exceptions, docstrings, comments, and comment-to-architecture traceability.
- Prefer the skill's established patterns over inventing repo-local patterns when the skill already covers the concern.

## Code Guardrails Skill

- Use the repo-local `$code-guardrails` skill as the default behavioral baseline for writing, reviewing, or refactoring code: read `.agents/skills/code-guardrails/SKILL.md` first, surface assumptions, prefer the simplest boring solution, keep changes surgical, finish cutovers cleanly without legacy leftovers, and define verifiable success criteria before implementing.

## Research Proactively

- Use the web search tool extensively in ambiguous situations or when stuck.
- Search early when facts, terminology, APIs, behavior, or external constraints
  are unclear, and verify assumptions instead of guessing.

## Execution Environment

- When a repo executable may depend on `.envrc`, credentials, or local runtime configuration, run it through `direnv exec .` unless the current shell already loaded the repo environment.
- Direnv trust is path-local. In a new clone or worktree, run `direnv allow` once before relying on `direnv exec .`.
- Apply this to any current or future executable entrypoint, including `examples/`, `workbench/`, `tests/`, `scripts/`, and similar repo directories.

## Compact Instructions

When compressing, preserve in priority order:

1. Architecture decisions (NEVER summarize)
2. Modified files and their key changes
3. Current verification status (pass/fail)
4. Open TODOs and rollback notes
5. Tool outputs (can delete, keep pass/fail only)

### Sub-agents Usage

- Wait for the sub-agents to finish and don't rush them.
- Actively delegate tasks to sub-agents — use Explorer for research and analysis, and Worker for execution and implementation.

## Git

- Never stage, unstage unless the user explicitly asks in the current turn.

## RTK

- Prefer `rtk` when an RTK equivalent exists and it preserves the command's runtime semantics.
- Prefer forms like `rtk git status`, `rtk cargo test`, and `rtk npm run build`.
- For interpreter- or env-sensitive Python commands, prefer `rtk proxy uv run ...` or plain `uv run ...`.
- Use `rtk gain` or `rtk gain --history` to inspect token savings.
- Use `rtk proxy <cmd>` when you need the raw command without RTK filtering or without RTK changing runtime selection.

@RTK.md
