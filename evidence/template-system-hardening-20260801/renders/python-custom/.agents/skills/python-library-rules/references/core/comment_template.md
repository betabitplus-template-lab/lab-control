---
name: comment-template
description: Template guidance for Python code comments below the file-docstring level. Use when you need consistent class docstrings, method docstrings, section banners, or inline comments.
---

# Comment Template

## Overview

Use this template for Python code comments below the file-docstring level.

Use `references/core/docstring_template.md` for file-level docstrings.

Use `references/core/comment_traceability_pattern.md` when comments should
mirror architecture docs and boundary intent.

## When To Use

Use this template when writing class docstrings, method docstrings, section
banners, or inline comments inside Python modules.

## Coverage

This file covers these comment types:

- class docstrings
- method and function docstrings
- section banners
- inline comments

It does not define file-level module, package, e2e, or workbench docstrings.
Use `references/core/docstring_template.md` for those.

## Core Rules (Code Style)

- Use sections extensively when a file has multiple meaningful parts, especially public API, helpers, parsing, formatting, setup, or assertions.
- Do not add section banners to small linear files; use them only when they clarify real conceptual boundaries.
- In Python helper `_` files, use section banners when the file contains multiple helper families such as request building, parsing, formatting, or protocol adaptation.
- In Python, use three-line `=` section banners for code sections, and size them to the Ruff 88-character line length including scope indentation.
- Example:
  `# ================================================================================`
  `# Public API`
  `# ================================================================================`

## Rules

- keep comments short and purposeful
- explain why, invariant, or preserved contract more often than mechanics
- add comments only where they make the architecture easier to see
- do not narrate obvious syntax, assignments, or control flow

## Class Docstrings

Use class docstrings to state ownership and invariants.

Prefer:

- what semantic boundary the type owns
- why that boundary stays centralized here
- what must remain true across calls

### Template

```python
"""Owns <semantic boundary>.

Why:
    <why this state or abstraction stays centralized>

Invariant:
    <what must remain true across calls>
"""
```

### Short Template

```python
"""Owns <semantic boundary> for one <lifecycle or request scope>."""
```

## Method And Function Docstrings

Use method and function docstrings to state purpose and preserved contract.

Prefer:

- why this operation exists in the larger lifecycle
- what boundary, invariant, or cross-cutting concern it preserves
- what meaning would be lost without it

### Template

```python
"""Preserve <concept or contract> so <larger system reason>."""
```

### Examples

```python
"""Preserve graceful degradation when every route is temporarily blocked."""
```

```python
"""Keep the normalized result stable across provider-native payload shapes."""
```

## Section Banners

Prefer section titles that mirror the reader's walkthrough, such as:

- `Request Models`
- `Policy Resolution`
- `Tool-loop Finalization`
- `Public API`

### Template

```python
# =============================================================================
# <Section Title>
# =============================================================================
```

## Inline Comments

Use inline comments only where architecture would otherwise become invisible.

Good inline comment targets:

- fallback policy
- snapshot boundaries
- capability normalization
- sync-async semantic parity
- failure attribution
- provider-specific workaround rationale

### Good

```python
# Preserve the first route as declared priority; shuffle only fallbacks.
```

```python
# Keep this workaround local so the public structured-output contract stays
# unchanged for callers.
```

### Not By Default

```python
# Increment the counter.
counter += 1
```

```python
# Loop through the routes.
for route in routes:
    ...
```
