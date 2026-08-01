---
name: comment-traceability-pattern
description: Reusable comment and docstring traceability patterns for Python libraries and services. Use when code comments should mirror architecture docs and boundary intent.
---

# Comment Traceability Patterns

## Overview

Use this guide for keeping code comments and docstrings tightly aligned with
the architecture docs and boundary intent.

Use `references/core/docstring_template.md` for file-level docstring shapes.

Use `references/core/comment_template.md` for class, method, section, and
inline comment shapes.

## When To Use

Use this guide when a codebase already has documented concepts, flows,
principles, or cross-cutting concerns and the code should make that
architecture visible at the point where it becomes executable.

## Core Patterns

### Layer Pattern

Map each documentation layer to one code-comment layer.

- `concepts/`
  module and class docstrings
- `principles/`
  invariant and boundary-purpose docstrings
- `flows/`
  section banners, function order, and orchestration comments

This keeps the code readable top-down instead of scattering architecture
details randomly.

### Shape Pattern

Let the templates own syntax and label order.
Let this pattern own why the comment system exists and how it maps to the
architecture.

- use `references/core/docstring_template.md` for file-level docstrings
- use `references/core/comment_template.md` for class, method, section, and
  inline comments
- do not duplicate the same template rules across multiple reference files

### Ordering Pattern

Arrange files so comments read as a walkthrough.

Prefer this order when it fits:

1. module docstring
2. shared constants or sentinels
3. request or state models
4. public orchestration
5. narrow helpers
6. low-level translation or parsing details

Within large helper files, use section banners to mirror the documented flow
rather than arbitrary implementation groupings.

### Traceability Pattern

Each important architecture concept should appear in code comments where it
materially shapes behavior.

That does not mean every file must mention every concept.
It means the concept should be visible where it becomes executable.

Examples:

- config snapshot rules appear where config is normalized or installed
- routing concepts appear where route order, waiting, fallback, or trace state
  are owned
- persistence concepts appear where semantic history is saved, restored, or
  projected back into requests
- graceful degradation appears where failures become retries, cooldowns, or
  fallbacks

### Comment Stack Pattern

Let each comment layer answer a different question.

- file docstring
  what boundary is this?
- class docstring
  what does this type own?
- method docstring
  what contract does this operation preserve?
- inline comment
  why does this local branch or workaround exist here?

This prevents multiple comment layers from repeating the same sentence in
slightly different words.

### Omission Pattern

Do not turn comments into a second copy of the docs.

Avoid:

- full theory dumps
- repeating docs paragraph-for-paragraph
- describing obvious mechanics
- adding architecture slogans with no local meaning

Each comment should connect one local implementation point to one larger
architectural reason.
