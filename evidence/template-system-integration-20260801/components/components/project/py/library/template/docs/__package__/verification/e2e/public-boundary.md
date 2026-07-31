---
name: public-boundary-e2e
doc_type: verification
description: E2E proof for the baseline public config boundary. Use when you need to confirm the starter public package can install and read config through supported imports.
---

# Public Boundary E2E

## Overview

This e2e slice proves the baseline package can install and read a runtime
config snapshot through the supported top-level public API.

## Proof

### Scenario

[test_public_config_pipeline.py](../../../../tests/[[[ package_name ]]]/e2e/public_boundary/test_public_config_pipeline.py)
runs the public config lifecycle through `[[[ package_name ]]]`.

### Checks

If a caller installs a config snapshot, then `get_config()` returns the same
public snapshot through the supported top-level import boundary.

Would fail if:

- config facade exports stopped resolving through the top-level package
- config installation no longer updated the active runtime snapshot
- the e2e test needed private imports to prove public behavior
