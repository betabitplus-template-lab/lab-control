# Scripts

Repo-local scripts live here only when the implementation is specific to this
repository. Shared development commands come from `py-lib-testkit` console
scripts.

## Shared Repo Config

`py_lib_testkit.get_project_tooling_config` is the single reader for repo-local tooling
metadata in `[tool.ternforge]` in `pyproject.toml`.

- Use it when behavior depends on the distribution name, the primary package,
  the package list, or the env var prefix.
- Do not hardcode project package names in reusable checks, smokes, or shared
  test support; read them from `[tool.ternforge]`.
- When the template is rendered or updated for another library, keep
  `[project].name` and `[tool.ternforge]` in `pyproject.toml` accurate; the
  shared checks and smoke commands should then follow that config.
- `package_names` supports future multi-package repos; `primary_package`
  remains the default import/smoke target.
- Keep this helper out of runtime package code under `src/`; it is only for
  repository tooling and test support.

Example:

```python
from py_lib_testkit import get_project_tooling_config

project_config = get_project_tooling_config()
package_name = project_config.primary_package
package_names = project_config.package_names
```

## Local Scripts

- `env/`
  Local contributor environment setup and health checks. `project_config.sh`
  reads `[tool.ternforge]` from `pyproject.toml`.
  Repos that declare `[tool.ternforge.secrets].env_files` load encrypted
  dotenv secrets through `scripts/env/secrets.sh`.

Use shared smoke commands directly:

```bash
uv build
uv run pytest tests/[[[ package_name ]]]/e2e/public_boundary -q --no-cov
```

Check and apply released Ternforge template updates with Copier:

```bash
uvx --from copier==9.17.0 copier check-update
uvx --from copier==9.17.0 copier update
```

Run structural and artifact checks directly when needed:

```bash
uv run py-lib-policy .
uv run py-lib-policy .
uv build
```

Use the running-loop diagnostic helper only for real workbench modules:

```bash
uv run python scripts/reproduce_running_loop.py workbench.[[[ package_name ]]].<module>
```
