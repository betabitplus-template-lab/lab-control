# Architecture Baseline

## Overview

This file defines the reusable architecture and engineering baseline for the
planned `_internal` runtime.

Most important rules:

- `<package_name>/__init__.py` stays the supported public facade.
- `_api/` defines the public contract.
- `_internal/` holds the private runtime.
- `_support/` is optional and holds package-specific private helpers only when
  they cannot belong in `_internal` or an installed shared runtime package.
- `workbench/` is live executable documentation and must not import from
  `src/`.

Interpret package paths against the live repo tree. If the repository uses a
`src/` root, follow the actual on-disk package locations instead of inventing a
different root.

Use `<package_name>` as a placeholder for the public package name discovered in
the target repository.

## Project Shape

- `<package_name>/__init__.py` is the supported public facade. External code
  should import from the top-level package, not private modules.
- `_api/` defines the public contract: router facade, config, sessions, errors,
  presets, and caller-facing models.
- `_internal/` holds the private runtime. Optional `_support/` holds
  package-specific private helpers only; shared py-lib runtime helpers should
  come from `py-lib-runtime` instead of local wrappers.
- `docs/<package_name>/architecture/concepts/` defines the main vertical slices
  of the system.
- `docs/<package_name>/architecture/principles/` defines the main design and
  refactor rules for private boundaries.
- `docs/<package_name>/architecture/flows/` defines the main end-to-end runtime
  flows across those boundaries.
- `workbench/` holds live probes and executable documentation. Use it to prove
  isolated features and real provider behavior before or alongside `src/`
  support. It is a separate concern and must not import from `src/`.
- `tests/<package_name>/e2e/` proves public behavior end to end across multiple
  boundaries.
- `tests/<package_name>/property_based/public_contract/` proves deterministic
  public invariants across many generated inputs.

## `_internal` Architecture

- `_internal/` should follow SOLID: clear ownership, narrow interfaces, and one
  reason to change per module.
- Keep core orchestration separate from implementation details. Move parsing,
  formatting, protocol glue, and other low-level mechanics into focused private
  helper files.
- Split `_internal/` into focused modules and submodules with clear boundaries.
  Python files should stay small. If a file grows mixed responsibilities or
  becomes too large, split it.
- When it makes sense, organize `_internal` modules, submodules, files, and
  classes around the main architecture concept slices. They are the preferred
  naming and grouping vocabulary when several good options exist, but they are
  not the only allowed structure.

## Config Management

- When the project has configurable runtime state, plan `_internal/config/` as
  the home for config mechanics.
- `_api/defaults.py` should remain declarative constants and catalogs only:
  no runtime state, install logic, cache invalidation, or execution behavior.
- `_api/config.py` should be a thin facade/re-export from the private root.
  It should not contain dataclass implementations, validation helpers, install
  lifecycle, logging, or cache invalidation.
- `_internal/config/models.py` owns immutable config dataclasses and snapshot
  shapes.
- `_internal/config/assembly.py` builds the built-in runtime config snapshot
  from `_api/defaults.py`.
- `_internal/config/validation.py` owns invariants, normalization helpers, and
  validation errors.
- `_internal/config/state.py` owns process-wide installed config state,
  `get_config()`/project-specific reads, and `install_config()`/project-specific
  updates.
- `install_config()` validates before replacing installed state, rejects
  non-config objects with `TypeError`, and clears runtime caches when those
  objects captured the previous snapshot.
- `_internal/config/__init__.py` and `_internal/__init__.py` should stay export
  maps only.
- Runtime modules should receive or capture validated snapshots instead of
  reading scattered defaults mid-operation.
- Keep config at a low `_internal` import-linter layer. If install-time cache
  invalidation requires reverse imports, plan the robust ignore:
  `"package._internal.config.** -> package._internal.**"`.

## Style

- Use section banners only for real conceptual phases in larger files. In
  Python, use three-line `=` banners sized to the Ruff 88-character limit.
- Document modules, classes, functions, and meaningful steps very widely with
  short docstrings and laconic inline comments so the code reads as a
  walkthrough and the why stays clear everywhere. Use section banners where
  they clarify real phases.

## Logging

- Library code must not configure global logging on import.
- Use the standard logging boundary. In Ternforge-managed Python libraries, feature
  modules should import `get_logger()` from `py_lib_runtime.logging`, not call
  `structlog.get_logger(...)` directly and not carry a local
  `_support/logging.py` wrapper.
- Emit stable structured events: one human-readable message, one stable
  classifier such as `event_type`, and a small flat field vocabulary. Keep
  event names consistent, for example `<system>.<area>.<subject>.<action>`.
- Bind stable operation context at the boundary where work starts and reuse it
  through the operation.
- Log state changes, decisions, retries, degraded paths, failures, and
  timing-relevant waits.
- Keep levels intentional: `debug` for flow, `info` for notable state changes,
  `warning` for recoverable degradation, and `error` for terminal failure.

Example format:

```python
log = logger.bind(operation="sync_request", entity_id="job-42")

log.info(
    "Operation started",
    event_type="runtime.operation.lifecycle.started",
    attempt=1,
)
```

## Exceptions

- Use layered exception modules: public types in `_api/errors.py`, private
  normalization or transport types in `_internal/errors.py`, and feature code
  translating into those shared types.
- Treat failures in three stages: validate local inputs early, normalize
  lower-level failures at explicit boundaries, then expose one stable typed
  exception to callers.
- Use built-in `TypeError` or `ValueError` for immediate caller mistakes. Use
  typed exceptions for runtime domain, configuration, integration, transport,
  and operational failures.
- Wrap third-party and transport exceptions before they cross a public
  boundary, especially at adapters, persistence boundaries, orchestration
  boundaries, and public facade entrypoints.
- Preserve causes with `raise ... from exc`.
- Use broad `except Exception` only at deliberate boundary-normalization
  points.
