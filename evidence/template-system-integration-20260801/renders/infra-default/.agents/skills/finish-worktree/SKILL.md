---
name: finish-worktree
description: Finish a git worktree cleanly. Use when Codex needs to merge a finished worktree branch, push the integration branch, remove the worktree, delete the branch, and prune stale worktrees.
---

# Finish Worktree

## Overview

Use this skill to close out a finished git worktree cleanly.

## Workflow

1. Inspect the current git state first: current branch, worktree list, remotes,
   and whether the working tree is clean.
2. Use explicit user arguments as hints for the worktree path, feature branch,
   remote, or target branch. Otherwise infer them from the repo state.
3. Read repo-specific guidance before acting. Prefer `AGENTS.md`, setup docs,
   branch protections, and current git configuration over generic defaults.
4. Stop and explain the blocker if the tree is dirty, the target branch is
   ambiguous, the merge is not safe to fast-forward, or the intended cleanup
   target is unclear.
5. Merge the finished branch into the repo's actual integration branch using
   safe non-interactive git commands, then push that branch to the intended
   remote.
6. After a successful push, remove the merged worktree, delete the merged
   feature branch, and run `git worktree prune`.
7. Summarize exactly what was merged, pushed, removed, and pruned.

## Constraints

- Do not use destructive commands such as `git reset --hard`.
- Do not bypass hooks or use `--no-verify`.
- Prefer the repo's documented integration branch instead of assuming `dev` or
  `main`.
- Prefer `origin` unless the repo state clearly indicates a different intended
  remote.
- Keep the workflow non-interactive whenever possible.

## Output

Report blockers before changing branches. After success, report the integration
branch, remote, merged branch, removed worktree path, deleted branch, and prune
result.
