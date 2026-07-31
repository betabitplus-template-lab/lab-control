---
name: logging-pattern
description: Reusable structured logging patterns for Python libraries and services. Use when you need a shared logging helper, stable event names, and a consistent event shape.
---

# Logging Patterns

## Overview

Use this guide for reusable structured logging patterns.

## When To Use

Use this guide when a project needs a shared logging helper, stable event
names, and a small consistent event shape.

## Core Rules (Logging)

- Library code must not configure global logging on import.
- Logs should be structured, stable, and machine-readable. Use `structlog`.
- Use one shared logging boundary. In Ternforge-managed Python libraries, that
  boundary is `py_lib_runtime.logging`.
- Library modules must obtain loggers through that boundary instead of
  importing and configuring `structlog` directly throughout the codebase.
- Every emitted event should have one stable event name or type and one
  consistent field vocabulary.
- Log state changes, important decisions, retries, degraded paths, failures,
  and timing-relevant waits.
- Prefer flat primitive fields and bind stable operation context once at the
  boundary where work begins.
- Never log secrets, credentials, tokens, raw personal content, or full
  request/response bodies unless they are explicitly redacted and required.
- Use log levels intentionally: debug for flow and decisions, info for notable
  state changes, warning for degraded but recoverable paths, error for terminal
  failures.
- Applications may configure handlers; libraries should remain safe by default.

## Core Patterns

### Structlog Pattern

Standard helper location for Ternforge-managed Python libraries:

- `py_lib_runtime.logging`

```python
from py_lib_runtime.logging import get_logger

logger = get_logger(__name__)
```

Direct `structlog.get_logger(...)` belongs inside the shared runtime helper
package itself, not across ordinary library modules.

Project-level setup for local scripts or test entrypoints:

```python
from py_lib_runtime.logging import configure_package_logging

configure_package_logging("package_name")
```

### Event Shape Pattern

```python
logger.info(
    "Operation started",
    event_type="runtime.operation.lifecycle.started",
)
```

Module usage pattern:

```python
from py_lib_runtime.logging import get_logger
from py_lib_runtime import preview_exception_message

logger = get_logger(__name__)


def run_sync() -> None:
    log = logger.bind(operation="sync_request", entity_id="job-42")
    log.info(
        "Operation started",
        event_type="runtime.operation.lifecycle.started",
    )
```

### Event Name Pattern

- `<system>.<area>.<subject>.<action>`

Examples:

- `runtime.operation.lifecycle.started`
- `runtime.operation.lifecycle.waiting`
- `runtime.operation.lifecycle.failed`

### Common Field Pattern

- `event_type`
- `operation`
- `entity_id`
- `attempt`
- `duration_ms`
- `wait_seconds`
- `error_type`
- `error_message`

### Example Shapes

Decision event:

```python
logger.info(
    "Operation started",
    event_type="runtime.operation.lifecycle.started",
    operation="sync_request",
    attempt=1,
)
```

Wait event:

```python
logger.info(
    "Operation waiting",
    event_type="runtime.operation.lifecycle.waiting",
    wait_seconds=2.5,
    reason="cooldown",
)
```

Failure event:

```python
logger.warning(
    "Operation failed",
    event_type="runtime.operation.lifecycle.failed",
    error_type="TimeoutError",
    error_message="operation timed out",
)
```

Boundary summary example:

```python
log = logger.bind(operation="sync_request", entity_id="job-42")

log.info(
    "Operation started",
    event_type="runtime.operation.lifecycle.started",
)

try:
    run_operation()
except TimeoutError as exc:
    log.warning(
        "Operation failed",
        event_type="runtime.operation.lifecycle.failed",
        error_type=type(exc).__name__,
        error_message=preview_exception_message(exc),
    )
    raise
else:
    log.info(
        "Operation completed",
        event_type="runtime.operation.lifecycle.completed",
        duration_ms=120,
    )
```

### Setup Pattern

Library modules should only call `get_logger(__name__)`. Configure handlers and
local log levels only at explicit process boundaries such as demos, workbench
scripts, e2e direct-module setup, or applications.

Starter-shaped py-lib repos can let shared test/direct-run setup read
repo-local logging policy from `pyproject.toml`:

```toml
[tool.py_lib_runtime.logging]
default_local_level = "DEBUG"
quiet_module_names = [ "asyncio", "httpx", "tenacity", "urllib3" ]
```

Keep that table absent when the shared defaults are enough. For one local
entrypoint override, pass `level=` or `json=` to `configure_package_logging()`
or `configure_logging()` at the entrypoint instead of changing library modules.
