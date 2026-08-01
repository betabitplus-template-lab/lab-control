---
name: usage
doc_type: usage
description: Representative public usage patterns for orbital kit. Use when you need examples of common caller workflows.
---

# Usage

## Overview

The package exposes the common config and public-error boundary before
product-specific behavior is added.

## Public Imports

```python
from orbital_kit import (
    OrbitalKitConfig,
    OrbitalKitError,
    get_config,
    install_config,
)

config = install_config(OrbitalKitConfig())
assert get_config() is config
```

## Runnable Examples

- [config_demo.py](../../examples/orbital_kit/config_demo.py)
  Run with: `uv run python examples/orbital_kit/config_demo.py`

## Next Public Slice

When the first real behavior lands, document caller-facing examples here using
only imports from `orbital_kit`. Keep private implementation details in
architecture docs, tests, or workbench probes, not in public usage examples.
