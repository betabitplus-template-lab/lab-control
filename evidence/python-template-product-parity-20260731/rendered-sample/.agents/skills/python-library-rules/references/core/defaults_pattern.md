---
name: defaults-pattern
description: Reusable built-in defaults patterns for Python libraries and services. Use when you need one clear home for shared default values consumed by config or runtime code.
---

# Defaults Patterns

## Overview

Use this guide for reusable defaults patterns.

## When To Use

Use this guide when a codebase needs one clear home for built-in values that
runtime configuration or execution code will consume.

## Core Rules (Defaults)

- Do not scatter defaults inside unrelated code.
- Prefer a centralized declarative defaults layer for shared default values.
- Built-in defaults must have one clear source of truth and live in `_api/defaults.py`.
- Keep the defaults layer focused on declarations, not runtime state or install
  mechanics, cache invalidation, logging, or execution behavior.
- Group defaults by concern so callers can tell which boundary they affect.
- Constructors and runtime code should read shared defaults from that layer
  instead of embedding repeated inline values.
- If a default value is mutable or nested, runtime assembly should copy or
  freeze it before use instead of sharing mutable module state.
- Top-level `__init__.py` may expose config types and helpers, but should avoid
  re-exporting raw default constants by default.

## Core Patterns

### Layer Pattern

Prefer three roles:

- `_api/defaults.py`
  Built-in declarations and catalog values.
- `_api/config.py`
  Optional thin public facade/re-export for configurable runtime state.
- `_internal/config/...`
  Normalization, validation, copying, freezing, and install mechanics.

### Grouping Pattern

- default selection
- behavior or policy
- tool or output limits
- catalog or registry data

Example:

```python
# _api/defaults.py
DEFAULT_REGION = "us"
DEFAULT_RETRY_MAX_ATTEMPTS = 5
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_SERVICE_URLS = {
    "primary": "https://api.example.com",
}
```

### Consumption Pattern

```python
# _internal/config/models.py
from package._api.defaults import DEFAULT_RETRY_MAX_ATTEMPTS


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = DEFAULT_RETRY_MAX_ATTEMPTS
```

### Mutable Data Pattern

```python
# _api/defaults.py
DEFAULT_SERVICE_URLS = {"primary": "https://api.example.com"}
```

```python
# _internal/config/models.py
def _default_service_urls() -> dict[str, str]:
    return dict(DEFAULT_SERVICE_URLS)
```
