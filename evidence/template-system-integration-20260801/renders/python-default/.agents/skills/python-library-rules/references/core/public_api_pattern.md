---
name: public-api-pattern
description: Reusable public API patterns for Python packages. Use when you need to shape a stable public boundary over a private implementation.
---

# Public API Patterns

## Overview

Use this guide for reusable public API patterns.

## When To Use

Use this guide when designing a stable public package boundary over a private
implementation.

## Core Rules (Public API)

- The public API must be minimal and stable.
- Use a stable public facade over a private core.
- Use the top-level `__init__.py` as the only supported public Python import
  entrypoint.
- `__all__` exists only in the top-level `__init__.py`.
- Public declarations must be separate from internal implementation.
- Use `_api` for private declaration and facade organization.
- Use `_internal` for product-specific private implementation.
- For packaged console scripts, treat command names as the public CLI API.
  Point `[project.scripts]` at an `_api.cli` facade and keep command
  implementation under `_internal`.
- Use `_support` only for package-specific private cross-cutting helpers and
  infrastructure that cannot cleanly live in `_internal` or an installed shared
  runtime package.
- In Ternforge-managed Python libraries, prefer direct `py_lib_runtime` imports for
  shared runtime helpers instead of local `_support` wrappers.
- If `_api` imports `_internal`, prefer one private-root import such as
  `from package._internal import Runtime` over deep `_internal.foo.bar` imports.
- If `_api/config.py` exists, keep it as a thin re-export from the private
  root; config implementation belongs in `_internal/config/`.
- Internal modules must be underscore-scoped and undocumented as public API.
- Separate public API, domain logic, infrastructure, adapters, and persistence concerns.

## Core Patterns

### Entry Point Pattern

Group top-level exports by role:

- execution entrypoints
- typed vocabulary and DTOs
- config and setup helpers
- sessions or persistence facades
- public exceptions
- optional presets or convenience builders

```python
# package/__init__.py
from package._api.client import Client
from package._api.config import Config, get_config
from package._api.errors import PackageError
from package._api.session import Session
from package._api.types import Request, Response

__all__ = [
    "Client",
    "Session",
    "Config",
    "Request",
    "Response",
    "PackageError",
    "get_config",
]
```

### Layer Pattern

If the facade imports private implementation, prefer re-exporting the needed
private entrypoints from `_internal/__init__.py` and importing from
`package._internal` rather than deep private paths.

For config facades, use the same private-root pattern:

```python
# _api/config.py
from package._internal import Config, get_config, install_config
```

Do not put dataclass implementations, validation helpers, install lifecycle,
logging, or cache invalidation in `_api/config.py`.

For CLI facades, keep the console-script declarations visible while leaving the
actual command behavior private:

```toml
[project.scripts]
package-check = "package._api.cli:check_main"
```

```python
# _api/cli.py
from package._internal import check_command as _check_command

CLI_ENTRYPOINTS = {"package-check": "check_main"}


def check_main() -> int:
    return _check_command()
```

Do not expose CLI entrypoint functions from the top-level `__all__` unless they
are also meant to be called as a supported Python API.

### Facade Pattern

Public facades should own caller-facing signatures and small input-shaping
logic, but not orchestration-heavy business logic.

```python
# _api/client.py
class Client:
    def __init__(self, config: Config) -> None:
        self._runtime = Runtime(config)

    def run(self, request: Request) -> Response:
        return self._runtime.run(request)
```

```python
# _api/session.py
class Session:
    @classmethod
    def load(cls, path: str | Path) -> "Session":
        store = SessionStore.load(path)
        obj = cls.__new__(cls)
        obj._store = store
        return obj
```

### Omission Pattern

Good:

```python
from package._api.client import Client
from package._api.types import Request, Response
```

Not by default:

```python
from package._internal.runtime import Runtime
from package._internal.store import SessionStore
from package._api.defaults import DEFAULT_TIMEOUT_SECONDS
```
