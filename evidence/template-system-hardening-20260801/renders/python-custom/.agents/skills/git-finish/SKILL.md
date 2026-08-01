---
name: git-finish
description: Finish Git work cleanly with commit, push, PR, or ship steps. Use when Codex needs to write a proper commit message, make one final real commit, let hooks run, push without bypassing checks, open or merge a PR, and verify release or CI completion.
---

# Git Finish

## Overview

Use this skill to finish local Git work cleanly.

Default mode is `push`: commit once cleanly, then push.

Treat the optional finish parameter as the highest step to complete:

- `commit`
  stop after the commit succeeds
- `push`
  commit, then push
- `PR`
  commit, push, then open a PR
- `ship`
  commit, push, open or reuse a PR, merge, then verify release and CI state

If no explicit parameter is given, use `push`.

If the user also wants a PR, treat that as part of the same finish flow.
Read the repository's `.github/pull_request_template.md` if it exists.
Use [references/pull_request_template.md](references/pull_request_template.md)
as the fallback PR body shape and as a reminder of the standard sections.

## Workflow

1. Inspect the current git state, current branch, remotes, and staged or
   unstaged changes first.
2. Read repo-specific Git guidance before acting. Prefer `AGENTS.md`, commit
   hooks, branch rules, `CONTRIBUTING.md`, and maintainer setup docs over
   generic defaults.
3. Stage only the intended changes and write a commit message that matches the
   repo's required format.
4. Commit once and let the normal commit hooks run. Do not run the same hook
   suites manually first unless the user explicitly asks.
5. If hooks fail, fix the issues and retry so the final history stays one real
   commit instead of a commit plus follow-up fix commits.
6. Before push, fetch the remote and confirm the branch is not behind its push
   target. If the remote moved, integrate it first so the final push stays
   fast-forward.
7. If a pre-push hook fails after a successful commit, fix the issue and update
   the not-yet-pushed commit so the final pushed history still lands as one real
   commit, not a commit plus fix commits.
8. If the finish mode is `push`, `PR`, or `ship`, push the intended branch to the
   intended remote.
9. If the finish mode is `PR` or `ship`, inspect the repo PR template and open
   or reuse the PR after the push succeeds.
10. Summarize the commit, branch, remote, push result, and PR result when
   applicable.

## Pull Request Flow

Use this section only when the finish mode is `PR` or `ship`.

1. Read `.github/pull_request_template.md` from the repo if it exists.
2. Fill the repo template rather than inventing a custom PR shape.
3. If `gh` is available and authenticated, use it for PR inspection and
   creation.
4. Otherwise use the local `git credential fill` path that already works for
   authenticated `git push`, then call the GitHub API with those credentials.
5. Check for an existing open PR for the same head/base pair before creating a
   new one.
6. Report the PR number and URL after success.

## Ship Flow

Use this section only when the finish mode is `ship`.

1. Complete the GitHub path end to end, including PR merge and release/sync
   automation.
2. Before merging, wait for required PR checks to pass. If checks fail, inspect
   the failing logs, fix the issue, amend or add the smallest appropriate
   commit according to repo policy, push, and wait again.
3. Merge with the repository's normal strategy. Prefer `gh pr merge` and avoid
   interactive consoles.
4. Watch the post-merge automation that matters for the repository: CI, release
   workflows, branch sync jobs, generated-template syncs, deployment checks, or
   package publishing. Use the repo's workflows and maintainer docs to identify
   what "done" means.
5. If the merge triggers downstream PRs or sync commits that are part of the
   requested scope, handle them with the same strict loop: wait for checks,
   merge, watch release/CI, and verify final state. Do not pull unrelated repos
   into scope unless the user asked.
6. Verify final remote and local state:
   - `main` and `dev` or the repo's equivalent protected branches are in the
     expected relationship, usually equal after release sync.
   - expected versions, tags, generated refs, and lockfiles moved or stayed put
     for the right reason.
   - latest relevant CI/release/sync runs are successful or intentionally
     skipped.
   - no open PR remains for the shipped branch or generated sync.
   - local branches are fast-forwarded and the worktree is clean.
7. If automation produces no product version bump because the change is
   template-only, docs-only, or dev-tooling-only, report that as expected rather
   than manufacturing a version change.

## Constraints

- Do not bypass hooks or use `--no-verify`.
- Do not create checkpoint commits that are meant to be fixed immediately after.
- Prefer safe non-interactive Git commands.
- Stop and explain blockers before committing or pushing if the repo state is
  ambiguous or the hooks expose real failures.

## Commit Message

- Match the repo's required commit format.
- If the repo uses Conventional Commits, keep the message in
  `<type>(<optional-scope>): <subject>`.
- Use the repo's allowed types if they are documented.
- If the repo uses standard `cz_conventional_commits`, accepted types are
  `build`, `bump`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`,
  `revert`, `style`, and `test`.

## Output

Report blockers before the commit. After success, report the final commit
message and commit hash. If the finish mode includes `push`, also report the
branch, remote, and push result. If the finish mode is `PR` or `ship`, also
report the PR number and URL. If the finish mode is `ship`, finish with the
merged PRs, release/tag/version results, branch parity, CI/release conclusions,
open-PR status, and local worktree status.
