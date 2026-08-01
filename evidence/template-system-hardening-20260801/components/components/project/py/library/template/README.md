# [[[ project_title ]]]

[[[ project_description ]]]

This project uses the shared py-lib project structure: source-layout
packaging, a small public package boundary, private implementation folders,
layered tests, package docs, runnable public API examples, local workbench
probes, and reusable project tooling.

## What It Provides

- `src/` source-layout packaging.
- A stable top-level public package entrypoint.
- `_api` declarations over private `_internal` implementation.
- A reusable config lifecycle with public re-exports and private snapshot state.
- Structured logging plus safe error/value previews from `py-lib-runtime`.
- Unit, integration, property-based, and e2e test folders.
- Reusable development and test tooling through `py-lib-testkit`.
- Package-specific tests under `tests/[[[ package_name ]]]/`.
- Runnable public API examples under `examples/[[[ package_name ]]]/`.
- Manual probes under `workbench/[[[ package_name ]]]/`.
- Package docs under `docs/[[[ package_name ]]]/`.
- Shared tooling metadata in `[tool.ternforge]`.
- Import-linter and smoke-check wiring.

The package starts with the common public boundary used across the py
libraries: version metadata, a package base error, config install/read helpers,
and a validated config snapshot type.

```python
from [[[ package_name ]]] import [[[ config_class_name ]]], get_config, install_config

config = install_config([[[ config_class_name ]]]())
assert get_config() is config
```

Add product-specific facades, DTOs, defaults, and vocabulary only when the
library has real behavior to ship.

## Quickstart

```bash
uv sync --group dev
uv run pytest
```

After the first render, review project metadata, repository URLs, environment
prefixes, and the first real public behavior slice before treating the package
as ready for product work.

## Project Customization

Review these project-specific values first:

- Distribution name: `[[[ project_name ]]]`
- Import package: `[[[ package_name ]]]`
- Public API objects in `src/[[[ package_name ]]]/__init__.py`
- Package docs under `docs/[[[ package_name ]]]/`
- Package tests under `tests/[[[ package_name ]]]/`
- Runnable examples under `examples/[[[ package_name ]]]/`
- Workbench probes under `workbench/[[[ package_name ]]]/`
- Project URLs in `pyproject.toml`
- Environment prefix: `[[[ env_prefix ]]]`
- Optional `[tool.py_lib_runtime.logging]` policy if local runs need
  non-default logging levels or quiet third-party modules

## Documentation

Start with [docs/[[[ package_name ]]]/README.md](docs/[[[ package_name ]]]/README.md)
for architecture, usage, dependency, and verification notes.
