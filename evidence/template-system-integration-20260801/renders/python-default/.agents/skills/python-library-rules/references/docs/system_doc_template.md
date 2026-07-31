---
name: system-doc-template
description: Template for one integrated top-level architecture document. Use when you need one high-level system story that explains how the system holds together and sends the reader into focused docs only where needed.
---

# System Doc Template

## Overview

Use this template for one integrated top-level architecture doc.

## When To Use

Use this template when one document should explain the whole product or package
at a high level and show how its main architectural concerns work together.

## File Shape

1. frontmatter
2. title
3. `Overview`
4. diagram question and one diagram when useful
5. one or more major runtime sections such as `Public Runtime Model`,
   `Execution Story`, or `Runtime Shape`

## Rules

- Treat this as the integrated entry point, not as a folder index.
- Build the doc around one stitching idea such as one request, one workflow,
  one state transition, or one lifecycle.
- Explain the whole system before sending the reader into focused architecture
  docs.
- Keep the prose high-level and durable across internal rewrites.
- Weave links to focused docs into the relevant paragraphs instead of adding
  grouped link catalogs.
- Keep guarantees stable and high-level, and fold them into the relevant
  runtime sections instead of ending with a summary-style invariant recap.

## Template

```md
---
name: system
doc_type: architecture
description: High-level system story for <product>. Use when you need one integrated architecture narrative before reading focused docs.
---

# System

## Overview

This document describes what the product does and why it exists.

Question this diagram answers: <one concrete system question>

```mermaid
flowchart LR
    A["..."] --> B["..."]
```


## Public Runtime Model

Short paragraph explaining the public model and the first major runtime
boundary. Link to focused docs inline only when the sentence benefits from the
deeper detail, for example [concepts/<concept-a>.md](concepts/<concept-a>.md).

## Execution Story

Short paragraph explaining the main lifecycle or orchestration story.

## Runtime Shape

Short paragraph explaining the main private runtime groups or durable
boundaries.
```
