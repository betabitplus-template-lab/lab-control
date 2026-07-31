---
name: exceptions-pattern
description: Reusable exception taxonomy and translation patterns for Python libraries and services. Use when you need a small stable exception surface with clear boundary wrapping rules.
---

# Exception Patterns

## Overview

Use this guide for reusable exception patterns.

## When To Use

Use this guide when a project needs a small stable exception taxonomy and clear
boundary translation rules.

## Core Rules (Exceptions)

- Keep one clear exception taxonomy for the whole codebase and use it
  consistently.
- Use layered package boundaries.
- Keep public exceptions in one dedicated public module such as
  `_api/errors.py`, and private normalization exceptions in one private module
  such as `_internal/errors.py`.
- Distinguish immediate caller-contract violations from runtime domain
  failures.
- Use built-in `TypeError` or `ValueError` for direct public input validation
  when the caller supplied an invalid type, value, or shape.
- Use typed exceptions for domain, configuration, integration, and operational
  failures that cross public runtime boundaries.
- Wrap third-party or transport exceptions before they cross a public boundary.
- Preserve original causes when wrapping lower-level failures.
- Error messages must explain what failed and why the caller should care.
- If exception message previews or truncation rules must stay consistent, use
  the shared runtime preview helpers when available, such as
  `py_lib_runtime.preview_exception_message`.
- Exception types should carry the stable context a caller or log consumer
  needs, but should not carry secrets or full payload bodies by default.
- Use broad `except Exception` only at deliberate boundary-normalization points,
  not inside ordinary business logic.

## Core Patterns

### Organization Pattern

Example layout:

```python
# _api/errors.py
class ApplicationError(Exception): ...


class ConfigurationError(ApplicationError): ...


class IntegrationError(ApplicationError): ...
```

```python
# _internal/errors.py
class RetryableTransportError(Exception): ...


class ResponseFormatError(Exception): ...
```

### Taxonomy Pattern

- caller contract violation
- invalid input
- configuration failure
- integration or transport failure
- domain operation failure

Caller-contract example:

```python
def validate_limit(limit: int) -> None:
    if limit <= 0:
        msg = "limit must be greater than zero."
        raise ValueError(msg)
```

### Wrapping Pattern

```python
try:
    payload = client.fetch()
except ExternalClientError as exc:
    raise IntegrationError("Request failed for upstream service.") from exc
```

- SDK or transport adapters
- persistence boundaries
- orchestration boundaries
- public facade entrypoints

Boundary example:

```python
from package._api.errors import IntegrationError
from package._internal.errors import RetryableTransportError


def fetch_record(client: object) -> dict[str, object]:
    try:
        return client.fetch()
    except RetryableTransportError:
        raise
    except ExternalClientError as exc:
        raise IntegrationError("Record fetch failed.") from exc
```

### Message Pattern

- what the caller did wrong or what operation failed
- what operation failed
- what boundary or dependency was involved
- what identifier or selector mattered

### Context Pattern

- `resource_id`
- `provider`
- `model`
- `status_code`

Do not attach secrets, tokens, cookies, or full request and response bodies by
default.

Context example:

```python
class IntegrationError(ApplicationError):
    def __init__(self, *, operation: str, resource_id: str, cause: Exception) -> None:
        self.operation = operation
        self.resource_id = resource_id
        self.cause = cause
        super().__init__(f"{operation} failed for resource '{resource_id}'.")
```
