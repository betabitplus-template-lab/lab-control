---
name: principles-doc-template
description: Template for one durable architecture principles doc. Use when you need short, refactor-stable rules for private design boundaries, ownership, or dependency direction.
---

# Principles Doc Template

## Overview

Use this template for one architecture principles doc.

## When To Use

Use this template when a project needs durable review or refactor guidance for
one internal design topic or principle family.

## File Shape

1. frontmatter
2. title
3. `Overview`
4. either `Rules` or one or more named principle sections
5. optional `Red flag` lines where a concrete failure mode adds new signal
6. optional `Invariants`

## Rules

- Keep the document shorter and more directive than overview docs.
- Translate generic principles into project-specific boundary names, ownership
  rules, and dependency directions.
- Do not cite private file paths, helper names, or current class names.
- Do not restate textbook theory at length.
- Do not retell the architecture overview.
- Prefer concrete rules and review questions.

## Template

```md
---
name: <principle-id>
doc_type: architecture
description: Durable <principle-family> guidance for <product> internals. Use when reviewing or refactoring private design boundaries.
---

# <Title>

## Overview

This document defines what this principle family means for the private design.

## Rules

- ...
- ...
- ...

Red flag: ...

## Invariants

- ...
- ...
- ...
```
