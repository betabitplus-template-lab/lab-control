---
name: plan-root-readme-template
description: Template for the root `plan/README.md` execution task. Use when creating the task doc that tells a future agent how to implement the plan to completion.
---

# Plan Root README Template

## Overview

Use this template for `plan/README.md`.

## When To Use

Use this template when the planning package needs a root task file that tells a
future implementing agent what to do, what rules to follow, and how to use the
rest of the `plan/` tree.

## File Shape

1. title
2. `Overview`
3. `Task`
4. `Rules`
5. `Working Method`
6. `Files`

## Rules

- Keep the file short, operational, and implementation-facing.
- Tell the implementing agent to finish the plan until the success criteria and
  pass criteria are met.
- Treat `references/protocol/05-final-state-and-pass-criteria.md` as the
  canonical source for the planning protocol's completion rules when writing
  this file.
- Tell the implementing agent to use the `python-library-rules` skill.
- Include this exact instruction:
  `Do not inspect, fetch, clone, diff against, or copy from any git history, remote branch, tag, commit, release artifact, or external version of this repo`.
- Tell the implementing agent not to stop at a phase checkpoint just because a
  phase became complete; the task is only complete when the roadmap and final
  cleanup success criteria and pass criteria are actually met, unless the user
  explicitly pauses or redirects the work.
- Tell the implementing agent to update plan checklists and verification bullets
  periodically, but only when the work is truly complete and the named checks
  have truly passed after the latest relevant changes.
- Tell the implementing agent to actively use and regularly review
  `plan/implementation-notes.md`.
- Tell the implementing agent to keep visible progress current during the
  phase and keep the active phase file plus `plan/implementation-notes.md`
  current during the work.
- Tell the implementing agent to start the earliest incomplete phase
  immediately after the minimum startup read set instead of re-proving that
  `_internal` is missing or re-discovering plan facts already captured.
- In `Files`, point only to the most important plan files a future agent should
  open first.

## Template

```md
# Plan Task

## Overview

These docs describe the execution task for implementing the planned
`_internal` runtime to completion.

Treat `plan/internal-discovery/` as the preserved contract and target-shape
input, and treat `plan/internal-implementation/` as the phased execution plan
to follow until the whole cutover is complete.

## Task

- Implement the plan fully until all success criteria in
  `plan/internal-implementation/00-roadmap.md` and
  `plan/internal-implementation/90-final-cleanup-and-cutover.md` are met.
- Preserve the supported public surface and all existing public proofs while
  replacing the private runtime.
- Use the project-local `$python-library-rules` skill in
  `.agents/skills/python-library-rules/` as the engineering baseline.

## Rules

- Do not inspect, fetch, clone, diff against, or copy from any git history,
  remote branch, tag, commit, release artifact, or external version of this
  repo.
- Treat the current repo tree and the current `plan/` docs as the only source
  of truth.
- Work phase by phase. Do not skip prerequisites, verification gates, or final
  cleanup.
- Do not stop at a phase checkpoint just because one phase became complete.
  The task is only complete when the success criteria and pass criteria in
  `plan/internal-implementation/00-roadmap.md` and
  `plan/internal-implementation/90-final-cleanup-and-cutover.md` are actually
  met, or when the user explicitly pauses or redirects the work.
- Mark checklist items and verification bullets complete only when the work is
  actually done and the named checks have really passed after the latest
  relevant changes.

## Working Method

- Read this file first.
- Read the discovery docs that define the current contract and target shape.
- Read `plan/internal-implementation/00-roadmap.md`, then execute the earliest
  incomplete phase file.
- Start implementation immediately after that minimum read set. Do not spend
  time re-proving that `_internal` is missing or re-discovering repo facts the
  plan already states; make the first phase-owned code, test, or doc change.
- Keep visible progress current during the phase: mark completed checklist
  items as soon as they are truly done, update the active phase file and
  `plan/implementation-notes.md` immediately when a phase finishes, and
  refresh both before any pause.
- Use [implementation-notes.md](implementation-notes.md) as active working
  memory and review it regularly.

## Files

- [internal-discovery/02-public-contract.md](internal-discovery/02-public-contract.md)
  Defines the supported public package boundary.
  Use it to preserve the caller-facing surface while `_internal` is rebuilt.
- [internal-discovery/03-preserved-functionality.md](internal-discovery/03-preserved-functionality.md)
  Lists the invariants and proof files that must stay green.
  Use it as the non-regression floor for each implementation phase.
- [internal-discovery/04-target-internal-architecture.md](internal-discovery/04-target-internal-architecture.md)
  Defines the target private package layout and ownership split.
  Use it to keep the implementation aligned with the intended final shape.
- [internal-implementation/00-roadmap.md](internal-implementation/00-roadmap.md)
  Defines phase order and whole-cutover success criteria and pass criteria.
  Use it to choose the next phase and understand when the full task is done.
- [implementation-notes.md](implementation-notes.md)
  Captures short-lived working notes, blockers, and recent verification
  results.
  Use it as active working memory and review it regularly.
```
