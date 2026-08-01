---
name: [[[ project_name ]]]-docs
doc_type: index
description: Package documentation index for [[[ project_title_lower ]]]. Use when you need to navigate architecture, usage, dependency, or verification docs.
---

# [[[ project_name ]]] Docs

## Overview

These docs start as a small package-documentation baseline. They should explain
real library behavior as soon as the first product slice lands.

## Files

- [architecture/README.md](architecture/README.md)
  Indexes the stable architecture docs.
  Use it to navigate system, concept, and flow documentation.
- [architecture/system.md](architecture/system.md)
  Explains the current package boundary and implementation structure.
  Update it when a real runtime model exists.
- [dependencies.md](dependencies.md)
  Explains direct runtime dependency roles.
  Keep it focused on shipped dependencies, not the full lockfile.
- [usage.md](usage.md)
  Shows supported public imports, caller-facing examples, and runnable example
  entrypoints.
  Extend it when product-specific public behavior exists.
- [verification/README.md](verification/README.md)
  Indexes the verification-oriented docs.
  Use it to choose between examples, tests, and workbench behavior.
