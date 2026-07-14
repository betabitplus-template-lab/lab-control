# Pilot risks and measured outcomes

| Risk | Measured outcome | Decision |
| --- | --- | --- |
| Production mutation | Controllers use an exact lab allowlist; source clone is detached and clean | Keep hard allowlists and separate App installation |
| File symlink portability | Text, templated, empty, and binary file symlinks render correctly | Supported where checkout preserves symlinks; CI covers three OS lanes |
| Executable file symlink | Copier dereferences content but does not preserve executable mode | Use executable Jinja wrappers with mode `755` |
| Directory symlink | Works when the resolved target remains inside the template tree; external target is forbidden | Permit only internal component directory targets |
| Jinja loader path | Includes are resolved from repository clone root, not `_subdirectory` | Use `template/_components/...` include paths |
| `_components` leakage | Exclusion and render tests verify it is loader-visible but absent downstream | Keep explicit `_exclude` entries and CI assertion |
| Component collisions | Static wiring creation rejects duplicate output paths | Treat any collision as a template design error, not runtime precedence |
| Private submodule auth | Separate lab App can recursively clone private templates/submodules in Actions and Renovate extraction | Keep absolute HTTPS URLs and App installation token |
| Component commit flood | Renovate follows `main` digest | Keep manual merge, grouping, and optional scheduling; no automerge |
| Release race | Exact-SHA controller checks requested SHA equals `origin/main` | Never create or move tags outside the controller |
| Copier conflicts | Renovate and downstream CI surface conflict markers | Never automerge template-update PRs |
| Unsafe templates | No `_tasks`; Renovate `allowScripts: false` | Keep templates declarative |
| Windows checkout | Symlink support depends on checkout capability | Matrix result decides whether native Windows is supported or WSL/devcontainer is required |
| Renovate beta submodule manager | Extraction is pinned and tested before live PRs | Keep a documented manual gitlink fallback |
| Old template tag deletion | Copier needs old refs for three-way updates | Treat released tags as immutable and permanent |
| Ephemeral diagnostic secret exposure | An early lab-only installation token appeared in an obsolete commit and expired automatically; current workflows redact tokens | Do not store raw controller logs; retain only sanitized tails and rotate App key if policy requires |

## No-go conditions

The architecture must be rejected if private recursive rendering is unreliable,
Renovate cannot update a gitlink deterministically, old/new tags do not reproduce
their pinned component revisions, wiring grows into a new assembler, or Copier
updates damage user changes without a reviewable conflict.

## Conditional decisions

- Native Windows may be replaced by WSL/devcontainer support if the Windows CI
  lane cannot preserve Git symlinks reliably.
- Explicit repository lists remain valid even if topic autodiscovery is not used.
- Template tags may remain manual/exact-SHA until release automation policy is
  accepted.
- A standard workflow may replace the beta submodule manager without changing
  the template/downstream architecture.
