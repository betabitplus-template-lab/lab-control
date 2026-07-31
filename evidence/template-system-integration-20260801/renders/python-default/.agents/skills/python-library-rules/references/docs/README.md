---
name: docs-index
description: Index of reusable documentation references for python-library-rules. Use when the task is about project docs rather than code comments or docstrings.
---

# Documentation References

## Overview

These docs describe the reusable project documentation guidance and templates.

## When To Use

Use this index when the task is about project docs and you need the narrowest
matching rules file or template.

## Files

- [docs_rules_pattern.md](docs_rules_pattern.md)
  Defines the shared documentation requirements and preferences.
  Use it to apply cross-cutting docs rules, then use the matching template
  for exact file shape.
- [docs_organization_pattern.md](docs_organization_pattern.md)
  Defines the common project docs and architecture-doc folder organization patterns.
  Use it to decide how to group docs into folders and top-level narratives.
- [index_doc_template.md](index_doc_template.md)
  Defines the template for folder indexes and `README.md` files.
  Use it to write short navigational indexes with `WHAT` then `WHY` file entries.
- [system_doc_template.md](system_doc_template.md)
  Defines the template for the default top-level integrated architecture doc.
  Use it to explain how the whole system holds together before diving into focused docs.
- [principles_doc_template.md](principles_doc_template.md)
  Defines the template for one durable internal-design principles doc used during review,
  refactoring, and internal rewrites.
  Use it to write stable design rules for private boundaries and refactor decisions.
- [dependencies_doc_template.md](dependencies_doc_template.md)
  Defines the template for one runtime dependency justification doc.
  Use it to explain why each shipped dependency exists and what role it serves.
- [vertical_slice_doc_template.md](vertical_slice_doc_template.md)
  Defines the template for one focused architecture slice.
  Use it to explain one concept or one flow without expanding into a whole-system story.
- [usage_doc_template.md](usage_doc_template.md)
  Defines the template for caller-facing usage docs.
  Use it to show representative public entry shapes and caller workflows.
