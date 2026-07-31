---
name: usage
doc_type: usage
description: Representative public usage patterns for [[[ project_title_lower ]]]. Use when you need examples of common caller workflows.
---

# Usage

## Overview

The package exposes the common config and public-error boundary before
product-specific behavior is added.

## Public Imports

```python
from [[[ package_name ]]] import (
    [[[ config_class_name ]]],
    [[[ error_class_name ]]],
    get_config,
    install_config,
)

config = install_config([[[ config_class_name ]]]())
assert get_config() is config
```

## Runnable Examples

- [config_demo.py](../../examples/[[[ package_name ]]]/config_demo.py)
  Run with: `uv run python examples/[[[ package_name ]]]/config_demo.py`

## Next Public Slice

When the first real behavior lands, document caller-facing examples here using
only imports from `[[[ package_name ]]]`. Keep private implementation details in
architecture docs, tests, or workbench probes, not in public usage examples.
