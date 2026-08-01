---
name: verification-index
description: Index of the verification references for python-library-rules. Use when the task is about verification docs, test tree placement, executable end-to-end tests, or live workbench probes.
---

# Verification References

## Overview

This folder holds the verification-focused references such as verification-doc
templates, test placement, executable e2e file shape, and live workbench
script structure.

The former shared testing and workbench baseline rules now live directly in
`e2e_test_template.md` and `workbench_script_template.md`.

## Files

- [test_file_template.md](test_file_template.md)
  Defines the shared pytest file template for unit, integration, and property-based tests.
  Use it to shape ordinary verification files under `tests/` with one reusable layout.
- [property_based_testing_doc_template.md](property_based_testing_doc_template.md)
  Defines the high-level property-based testing strategy doc template.
  Use it to describe invariant-driven checks over generated inputs and stable rules.
- [verification_doc_template.md](verification_doc_template.md)
  Defines the proof-oriented verification doc template, including the repeated
  proof-flow shape and proof-review sections for per-test evidence blocks.
  Use it to write proof docs that show what a verification set actually proves.
- [tests_routing_pattern.md](tests_routing_pattern.md)
  Defines the stable placement rules for the `tests/` tree.
  Use it to decide where helpers, support modules, and e2e files belong.
- [e2e_test_template.md](e2e_test_template.md)
  Defines the executable end-to-end test file template.
  Use it to build replay-backed scenario tests with one standard executable
  shape and to load the former testing baseline rules.
- [workbench_script_template.md](workbench_script_template.md)
  Defines the manual live workbench script template.
  Use it to build one focused live probe for a real behavior or dependency
  question and to load the former workbench baseline rules.
