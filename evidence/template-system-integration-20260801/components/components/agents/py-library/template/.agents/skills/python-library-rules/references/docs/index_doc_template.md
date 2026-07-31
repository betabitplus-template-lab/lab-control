---
name: index-doc-template
description: Template for folder indexes and README.md files. Use when you need a short navigational document that explains what belongs in one folder.
---

# Index Doc Template

## Overview

Use this template for folder indexes and `README.md` files.

## When To Use

Use this template when a doc exists mainly to explain what belongs in one
folder and where each document should send the reader next.

## File Shape

1. frontmatter
2. title
3. `Overview`
4. `Files`

## Rules

- Do not put deep architecture prose here.
- Do not add diagrams to index docs.

## Template

```md
---
name: <index-id>
doc_type: index
description: Index of the <topic> docs. Use when you need to find the right <topic> document.
---

# <Title>

## Overview

These docs describe what belongs in this folder.

## Files

- [first-doc.md](first-doc.md)
  Explains one focused concern.
  Use it to understand why that concern matters in this folder.
- [second-doc.md](second-doc.md)
  Explains another focused concern.
  Use it to find the next detail you need without scanning unrelated docs.
```
