---
name: core-index
description: Index of the core library design, code-structure, and runtime references for python-library-rules. Use when the task is about package boundaries, defaults, config, logging, exceptions, docstrings, comments, or the overall engineering baseline.
---

# Core References

## Overview

This folder holds the main engineering references that shape a Python
library's package boundary, code-comment system, runtime behavior, and shared
baseline.

The former shared engineering baseline now lives directly in the focused files
below.
For testing and workbench baseline rules, read `../verification/README.md`.

## Files

- [public_api_pattern.md](public_api_pattern.md)
  Defines the public package boundary and facade patterns.
  Use it to shape a small stable public surface over private implementation
  code and to load the former public API baseline rules.
- [defaults_pattern.md](defaults_pattern.md)
  Defines the declarative built-in defaults patterns.
  Use it to keep shared default values in one clear place instead of
  scattering them, including the former defaults baseline rules.
- [config_pattern.md](config_pattern.md)
  Defines the configuration layering and runtime snapshot patterns.
  Use it to separate built-in defaults, public config input, and validated
  runtime state, including the former configuration baseline rules.
- [logging_pattern.md](logging_pattern.md)
  Defines the structured logging helper and event-shape patterns.
  Use it to keep logs stable, shared, and machine-readable across the codebase,
  including the former logging baseline rules.
- [exceptions_pattern.md](exceptions_pattern.md)
  Defines the exception taxonomy and boundary translation patterns.
  Use it to keep failure types small, clear, and consistent across public
  boundaries, including the former exceptions baseline rules.
- [docstring_template.md](docstring_template.md)
  Defines the Python file docstring templates.
  Use it to write short file-level docstrings that explain purpose without
  excess detail, including the former documentation baseline rules.
- [comment_template.md](comment_template.md)
  Defines the class, method, section, and inline comment templates.
  Use it to write comments only where they add real local signal, including
  the former code-style rules for section banners and file organization.
- [comment_traceability_pattern.md](comment_traceability_pattern.md)
  Defines how code comments and docstrings should mirror architecture docs and boundary intent.
  Use it to keep code-level explanations aligned with architecture intent.
