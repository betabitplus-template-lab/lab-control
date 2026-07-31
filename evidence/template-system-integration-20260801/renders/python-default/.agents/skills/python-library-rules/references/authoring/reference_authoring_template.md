---
name: reference-authoring-template
description: Template for maintaining the reference set inside this skill. Use when you need to classify, name, split, merge, or rewrite reference files under references/.
---

# Reference Authoring Template

## Overview

Use this guide when maintaining the reference tree inside this skill.

## When To Use

Use this template when you need to decide whether a reference should be a
pattern or a template, how it should be named, and whether it should stay
separate or be merged with another file.

## Semantic Folders

Choose the folder before choosing the file kind.

### `core/`

Use for the main library design and runtime references:

- public boundary
- defaults and config
- logging and exceptions
- code comments and docstrings
- broader engineering baselines

### `verification/`

Use for references that shape how behavior is proved or explored:

- test placement
- e2e file structure
- workbench script structure

### `docs/`

Use for references that shape written project documentation:

- project docs rules
- docs page templates

### `authoring/`

Use only for references that explain how to maintain this reference tree
itself.

## Reference Kinds

### Pattern

Use a pattern when the file explains:

- a reusable boundary
- an organization rule
- a decision shape
- a grouped baseline

Rules-heavy references are still patterns, not a third kind.

Examples:

- `core/public_api_pattern.md`
- `core/logging_pattern.md`
- `docs/docs_rules_pattern.md`

### Template

Use a template when the file should give the reader a direct structure to
follow or copy.

Examples:

- `core/docstring_template.md`
- `verification/e2e_test_template.md`
- `docs/system_doc_template.md`

## Naming Rules

- Use suffix-style names.
- Use `<topic>_pattern.md` for patterns.
- Use `<topic>_template.md` for templates.
- Keep names short and concrete.
- Reserve `README.md` for indexes only.
- For `README.md` indexes, follow `docs/index_doc_template.md`, including `WHAT` then `WHY` file entries.

## Shared Format

Every reference file should include:

1. YAML frontmatter with only `name` and `description`
2. title
3. `Overview`
4. `When To Use`
5. the file's real working sections

## When To Split Or Merge

- Split a file only when two concerns no longer share the same selection logic.
- Merge files when their difference is mostly cosmetic or section naming.
- Prefer one stronger file over several weakly distinct files.
- Keep authoring guidance minimal; the reference tree should explain the skill,
  not itself.
- Add architecture subfolders only when each folder groups multiple docs with a
  clearly different reading purpose.

## Classification Examples

- If the reader needs to understand how a public boundary should be organized,
  write a pattern.
- If the reader needs a copyable file layout, write a template.
- If the file defines a grouped baseline such as engineering or docs rules,
  write a pattern, not a special third category.
