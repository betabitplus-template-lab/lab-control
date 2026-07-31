---
name: dependencies
doc_type: architecture
description: Justification for the runtime dependencies declared by [[[ project_name ]]]. Use when you need to understand what each shipped dependency supports.
---

# Dependencies

## Overview

The baseline includes the common runtime support used by the py libraries:
safe preview helpers, structured logging mechanics, and retry logging callback
adapters. Add shipped dependencies beyond these only when they support real
public behavior or a real private runtime concern.

## Dependency Roles

| Package          | Why it is shipped                                                   | Status          |
| ---------------- | ------------------------------------------------------------------- | --------------- |
| `py-lib-runtime` | provides shared previews, logging mechanics, and retry log adapters | support runtime |

## Rules

- A shipped dependency should map to a named runtime slice or support concern.
- Dependency docs should explain role and boundary, not every call site.
- Remove dependencies that no longer support the package baseline or a real
  project slice.
