---
name: configuration-pattern
description: Reusable configuration patterns for Python libraries and services. Use when you need a stable layering between built-in defaults, public config objects, and private runtime state.
---

# Configuration Patterns

## Overview

Use this guide for reusable configuration patterns.

## When To Use

Use this guide when configuration needs a stable layering between built-in
defaults, public config objects, and private runtime state.

## Core Rules (Configuration)

- A separate config facade is optional and should exist only when the project
  needs configurable runtime state.
- Use `_api/defaults.py` for declarative built-in constants and catalogs.
- Use `_api/config.py` only as a thin config facade/re-export.
- Use `_internal/config/` for config mechanics.
- Keep built-in default declarations separate from runtime configuration
  objects.
- Do not put model implementation, validation, install lifecycle, logging, or
  cache invalidation in `_api/config.py`.
- Normalize and validate public config input at construction boundaries.
- Prefer immutable installed config state after validation.
- If config is process-wide, install it explicitly and keep reads side-effect
  free.
- Runtime execution should consume a validated config snapshot instead of
  reading scattered defaults or mutable global config mid-operation.
- If installing config invalidates runtime objects built from the previous
  snapshot, clear those caches inside private config lifecycle code.

## Core Patterns

### Layer Pattern

- `_api/defaults.py`
  Built-in declarative constants and catalogs only.
- `_api/config.py`
  Optional public config facade; re-export from the private root only, for
  example `from package._internal import Config, get_config, install_config`.
- `_internal/config/models.py`
  Immutable config dataclasses and snapshot shapes.
- `_internal/config/assembly.py`
  Built-in runtime snapshot assembly from `_api/defaults.py`.
- `_internal/config/validation.py`
  Invariant checks, normalization helpers, and validation errors.
- `_internal/config/state.py`
  Process-wide installed config state and install/read lifecycle.
- `_internal/config/__init__.py`
  Export map for config internals only.
- `_internal/__init__.py`
  Narrow private-root export map for names consumed by `_api`.

### Construction Pattern

```python
@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ConfigurationError("timeout_seconds must be greater than 0.")
```

### Mutable Data Pattern

Copy or freeze mappings and nested structures before storing installed config.

```python
def _default_endpoints() -> dict[str, str]:
    return dict(DEFAULT_ENDPOINTS)
```

### Install Pattern

```python
_installed_config = build_default_config()


def get_config() -> RuntimeConfig:
    return _installed_config


def install_config(config: object) -> RuntimeConfig:
    if not isinstance(config, RuntimeConfig):
        raise TypeError("install_config() expects a RuntimeConfig instance.")
    validate_config(config)
    global _installed_config
    _installed_config = config
    clear_runtime_caches_that_captured_previous_snapshot()
    return _installed_config
```

### Import-Linter Pattern

Keep config at a low `_internal` layer. If install-time cache invalidation
needs a reverse import into runtime modules, keep the exception explicit and
robust to target-module renames:

```toml
ignore_imports = [
  # Installing config invalidates runtime objects built from the previous
  # snapshot. Keep the exception scoped to config while allowing invalidation
  # target modules to move without changing the layer map.
  "package._internal.config.** -> package._internal.**",
]
```

Run `lint-imports` after config-boundary changes.

### Testing Pattern

- Test config behavior through the public root package.
- Pin that installing a config replaces the active public snapshot.
- Pin that installing a non-config object raises `TypeError`.
- Pin cache invalidation behavior when runtime objects capture config snapshots.
- Keep tests about behavior, not private file placement.
