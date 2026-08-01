---
name: docstring-template
description: Template guidance for Python file docstrings. Use when you need short, purposeful file-level docstrings for modules, package boundaries, end-to-end tests, or workbench scripts.
---

# Python File Docstring Template

## Overview

Use this template for Python file docstrings.

## When To Use

Use this template when writing Python file docstrings for regular modules,
package boundaries, e2e scripts, or workbench scripts.

## Coverage

This file covers these Python file types:

- regular modules such as `module.py`
- package files such as `package/__init__.py`
- e2e scripts under `tests/.../e2e/`
- workbench scripts under `workbench/...`

It does not define one single template for every Python comment.
Use the section that matches the file type.

## Core Rules (Documentation)

- Follow `references/core/comment_template.md` in full for class, method,
  section, and inline comments when they add real signal.
- Follow `references/core/comment_traceability_pattern.md` when code comments
  and docstrings should mirror architecture docs and boundary intent.
- Keep docs short.

## Core Rules

- keep docstrings short and useful
- explain boundary purpose, not obvious code behavior
- use a short summary line first
- include only sections that add real information
- keep file docstrings compatible with the wider comment system:
  file docstrings explain the boundary role, lower-level comments explain
  invariants and local decisions
- add `Examples` only when usage is not obvious

## Standard Modules

Use this pattern for regular Python modules.

### Sections

Use these sections in this order when they are needed:

1. `Why`
2. `When to use`
3. `How`
4. `Notes`
5. `Examples`

Do not force all sections into every file.

- regular modules often need only `Why`
- `When to use` is optional and should explain import or boundary guidance only
  when that guidance is not obvious
- `How` is optional and should explain key usage shape, placement rule, or
  important constraint only when it adds real signal beyond the summary and
  `Why`
- `Notes` is optional and should hold only the most important caveats,
  invariants, or failure-boundary notes when they matter
- keep `Notes` short; one note is common, but two or a few is fine when they
  add real signal
- add `Examples` only when usage is not obvious
- `__init__.py` files are a special case

### Template

```python
"""<short module summary>.

Why:
    <why this module exists>

When to use:
    <when another module should import or rely on it>

How:
    <key usage shape, placement rule, or important constraint>

Notes:
    <short high-signal caveat, invariant, or boundary note when needed>

Examples:
    <short example if needed>
"""
```

### Example

```python
"""Reusable HTTP retry helpers.

Why:
    Keeps retry policy in one place so callers reuse the same backoff and
    timeout defaults.

When to use:
    Import this module when a service client needs standard retry behavior for
    transient request failures.

How:
    Use `build_retry_session()` instead of defining retry adapters in each
    caller.

Notes:
    Retries are for transient failures only, not caller validation errors.

Examples:
    from http_retry import build_retry_session
    session = build_retry_session()
"""
```

### Smaller Example

```python
"""Provider vocabulary declarations.

Why:
    Keeps the public provider names stable and centralized.
"""
```

## Package `__init__.py`

Use a shorter package docstring for `__init__.py`.

- explain why the package exists
- describe what belongs in this package
- describe what does not belong here when the boundary matters
- add examples only if the package exposes a non-obvious public import surface

### Example

```python
"""Shared test support.

Why:
    Holds reusable test infrastructure shared across multiple projects.

What belongs here:
    Generic setup, replay, and console helpers.

What does not belong here:
    Project-specific builders, assertions, or fixture helpers.
"""
```

## E2E And Workbench Script Docstrings

Do not reuse the regular-module template for e2e scripts or workbench scripts.

These file docstrings should document scenario coverage, not generic module
usage. They should also capture the highest-signal success criteria, because an
e2e or workbench script may later become the main source of truth for that
scenario.

### Sections

Use these sections for e2e and workbench scripts:

1. `Why`
2. `Covers`
3. `Checks`
4. `Notes` (only when needed)
5. `Examples`

Workbench scripts use this same pattern.
The difference is file structure, not docstring shape.

### What `Covers` Should Include

`Covers` should stay short and use neutral labels such as:

- `Area`: feature, workflow, subsystem, or integration boundary
- `Behavior`: the user-visible behavior under test
- `Interface`: public entry point, command, endpoint, UI flow, or API surface

Use only the lines that add signal.

### What `Checks` Should Include

`Checks` should mirror what the scenario actually proves.

- keep it as short as the proof surface allows
- for e2e files, cover every meaningful assertion or assertion cluster from the
  `Assertions` section
- for workbench files, cover every meaningful validated field, derived flag,
  or observed success condition the script uses as manual proof
- if several adjacent `assert` lines prove one indivisible contract point, they
  may share one `Checks` line
- do not omit a proved outcome just because it feels low-level if the file
  explicitly asserts it
- prefer contract wording over raw implementation wording, while still staying
  specific enough to match the assertions
- write each line as explicit `If <condition>, then <consequence>.`
- keep one meaningful condition-to-consequence statement per line
- use as many lines as needed to cover the asserted contract clearly

### Template

```python
"""<Project or workbench> scenario: <short description>.

Why:
    <what user-visible behavior this scenario proves>

Covers:
    Area: <feature, workflow, or subsystem>
    Behavior: <behavior under test>
    Interface: <public boundary exercised>

Checks:
    If <condition>, then <highest-signal expected outcome 1>.
    If <condition>, then <highest-signal expected outcome 2>.

Notes:
    <only if runtime prerequisites or replay caveats matter>

Examples:
    Run manually:
        python path/to/test_file.py

    Run as test:
        pytest path/to/test_file.py
"""
```

### Example

```python
"""CSV import workflow scenario.

Why:
    Verifies that a CSV import completes and produces normalized records.

Covers:
    Area: import workflow
    Behavior: file upload, validation, persisted output
    Interface: CLI entry point and saved output file

Checks:
    If rows are accepted, then they are normalized into the expected record
    shape.
    If rows are invalid, then they are reported without aborting the whole
    import.
    If the import succeeds, then the saved output contains the expected number
    of accepted records.

Notes:
    Live manual runs require the sample CSV fixture.

Examples:
    Run manually:
        python path/to/test_file.py

    Run as test:
        pytest path/to/test_file.py
"""
```

## Quick Choice

- use `Standard Modules` for ordinary `.py` files
- use `Package __init__.py` for package boundary files
- use `E2E And Workbench Script Docstrings` for executable e2e and workbench
  scripts
