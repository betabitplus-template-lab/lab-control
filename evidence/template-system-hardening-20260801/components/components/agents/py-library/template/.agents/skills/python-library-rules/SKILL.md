---
name: python-library-rules
description: Reusable engineering rules for designing, reviewing, and refactoring Python libraries or services with a stable public API over a private core. Use when Codex needs to shape package boundaries, defaults and config layering, structured logging, exception taxonomy, e2e and workbench patterns, test tree routing, or Python code comments and docstrings in a repo-agnostic way.
---

# Python Library Rules

## Overview

Apply a strict reusable baseline for Python libraries and services.
Read `references/core/README.md` first, then load only the narrower pattern or
template files needed for the task.


## When To Use

Use this skill when designing, reviewing, or refactoring a Python library or
service that needs a stable public API over a private core.

Use this skill when the task touches package boundaries, defaults and config
layering, structured logging, exception taxonomy, test-tree placement,
end-to-end test shape, workbench script shape, or Python code comments and
docstrings.

## Workflow

1. Read `references/core/README.md` before planning, editing, or reviewing.
2. If the task touches tests or workbench, also read
   `references/verification/README.md`.
3. Read the focused files from `Baseline Map` that match the task instead of
   looking for one umbrella baseline file.
4. Identify the narrowest relevant reference file instead of loading the whole
   reference tree.
5. Apply the rules directly in the codebase with the simplest effective
   implementation.
6. Keep the public surface stable and keep internal implementation details out
   of the supported package boundary.

## Core Expectations

- Prefer one supported top-level package entrypoint and a thin public facade
  over private runtime code for Python imports.
- For packages that ship console scripts, treat installed command names as the
  public CLI boundary. Keep script targets behind an `_api.cli` facade and keep
  command implementation under `_internal`.
- Keep `_api`, `_internal`, and optional `_support` responsibilities clearly
  separated. Prefer no local `_support` package when shared runtime helpers or
  private product modules are a better fit.
- Keep built-in defaults declarative and separate from runtime config state.
- Keep `_api/config.py` as a thin re-export facade when config mechanics live
  in `_internal/config/`.
- Normalize and validate config at construction boundaries, then run against a
  validated snapshot.
- Use the standard structured logging boundary and one stable event vocabulary.
  In Ternforge-managed Python libraries, import `py_lib_runtime.logging` directly
  instead of carrying local logging wrappers.
- Keep one small exception taxonomy and translate lower-level failures at
  explicit boundaries.
- Test public behavior, not internal implementation details.
- Run import-linter after package-boundary or config-lifecycle changes.
- Keep docs and docstrings short, purposeful, and boundary-aware.
- During refactors, do not add backward-compatibility layers, dead code, or
  transitional comments.

## Reference Map

- `references/core/README.md`
  Load first for the core package-boundary, runtime, and code-comment maps.
- `references/core/public_api_pattern.md`
  Load for public-boundary and facade rules.
- `references/core/defaults_pattern.md`
  Load for declarative built-in defaults rules.
- `references/core/config_pattern.md`
  Load for configuration layering and runtime snapshot rules.
- `references/core/logging_pattern.md`
  Load for structured logging helper and event-shape rules.
- `references/core/exceptions_pattern.md`
  Load for exception taxonomy and boundary-translation rules.
- `references/core/comment_template.md`
  Load for lower-level comment rules and the former code-style section-banner
  rules.
- `references/core/docstring_template.md`
  Load for file-docstring rules and the former documentation baseline.
- `references/core/comment_traceability_pattern.md`
  Load when code comments and docstrings should mirror architecture intent.
- `references/verification/README.md`
  Load for the verification and workbench reference map.
- `references/verification/tests_routing_pattern.md`
  Load for test-tree placement and import-routing rules.
- `references/verification/e2e_test_template.md`
  Load for executable e2e file shape and the former testing baseline.
- `references/verification/workbench_script_template.md`
  Load for live workbench file shape and the former workbench baseline.
- `references/README.md`
  Load when you need the top-level map of the bundled references.
- `references/docs/README.md`
  Load when the task is about project-doc structure, templates, or rules.
- `references/authoring/README.md`
  Load when maintaining the skill reference tree itself.
- `scripts/check_docs_shape.py`
  Run when validating a docs tree against the bundled docs-shape rules or
  wiring an on-demand CLI or pre-commit hook for those checks.

## Execution Notes

- Preserve existing intentional user changes unless explicitly asked to rewrite
  them.
- Prefer concise edits that enforce the architecture instead of adding extra
  abstraction.
- If a task touches multiple concerns, read
  the matching focused files from `Baseline Map` plus one focused pattern or
  template per concern.

<!-- component update v0.2.0 -->
