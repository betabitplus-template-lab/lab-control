# Discovery Stage

## Overview

This file defines the current-state discovery requirements for the planning
stage.

Most important rules:

- Create `plan/internal-discovery/`.
- Use only the current tree as input.
- Treat `_api`, present package-specific `_support`, architecture docs,
  workbench, e2e tests, and public-contract property tests as the contract.
- Record facts and planned boundaries, not brainstorming.

## Discovery Folder

- Create `plan/internal-discovery/`.
- Use it for current-state notes, preserved-contract notes, and target-shape
  planning for `_internal`.
- Use only the current tree as input. Do not inspect git history and do not
  plan from previous implementations.

## Root Plan Files

- Use `references/plan_root_readme_template.md` for `plan/README.md`.
- Use `references/implementation_notes_template.md` for
  `plan/implementation-notes.md`.
- `plan/README.md` is the root execution task for the future implementing
  agent.
- `plan/implementation-notes.md` is active working memory for the future
  implementing agent.
- Follow the template requirements instead of restating those rules elsewhere in
  the plan package.

## Required Discovery Files

- `01-workbench-live-probes.md`:
  analyze `workbench/` as live executable documentation, record what each probe
  already proves in isolation, and capture solution-specific details,
  workarounds, constraints, and implementation implications that must be
  respected later.
- `02-public-contract.md`:
  inspect `_api/` and summarize the expected public contract, including facade
  entrypoints, caller-facing models, config surface, sessions, normalized
  outputs, and public errors. When config exists, record what belongs in
  `_api/defaults.py`, what `_api/config.py` should re-export, and what private
  config names must be available through `_internal/__init__.py`.
- `03-preserved-functionality.md`:
  inspect current e2e and property-based tests and list all required behavior
  that must be preserved. Treat this as the non-regression checklist.
- `04-target-internal-architecture.md`:
  plan the future `_internal` architecture in advance, including module and
  submodule boundaries, orchestration files, helper files, dependency
  directions, config lifecycle ownership when applicable, and mapping to the
  architecture concept slices.
- `05-internal-docs-coverage.md`:
  plan where docstrings, inline comments, and section banners must go so the
  implementation reads as a walkthrough and explains why at every meaningful
  step.
- `06-internal-logging-coverage.md`:
  plan where log messages must be emitted across `_internal`, which event types
  and bound fields are needed, and which important paths must always be logged.
- `07-internal-exception-plan.md`:
  plan the needed exceptions, their ownership, boundary-normalization points,
  cause-chaining rules, and message expectations.
- `08-principles.md`:
  explain in practical detail how the declared principles should be expressed
  inside `_internal`. This should be a useful implementation guide, not general
  theory.

## Discovery Rules

- Keep discovery notes concrete and implementation-useful.
- Record facts, required constraints, and planned boundaries, not loose
  brainstorming.
- Prefer naming exact preserved symbols and seams when they are inferable from
  the live tree: imported `_internal` names, public fields, method names,
  trace fields, event types, exception types, config attributes, env vars, and
  helper hooks.
- Mirror the main vertical slices from
  `docs/<package_name>/architecture/concepts/` where that improves planning and
  navigation.
- Add links to implementation files only where the current discovery sentence
  or bullet directly hands off a constraint, proof, ownership, or doc to a
  specific phase. Do not add generic crosswalk sections.
