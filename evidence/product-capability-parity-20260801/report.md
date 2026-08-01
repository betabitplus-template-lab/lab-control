# Complete product capability parity

## Result

PASS. Every inventoried legacy capability has exactly one accepted disposition, split packages pass independent acceptance, and all four frozen downstream suites retain exact results after the atomic migration.

## Reproducibility inputs

The unresolved 73-row capability inventory, the frozen structural inventory, and the extractor that produced it are committed under `experiments/product-capability-parity/`. The structural snapshot records the exact `betabit-notes`, `py-lib-starter`, and `lab-control` revisions used by this experiment.

## Capability dispositions

| Disposition | Count |
|---|---:|
| `preserved` | 40 |
| `standard_replacement` | 23 |
| `intentional_removal` | 10 |

No unresolved, deferred, representative-only, or sample-only disposition is allowed.

## Split packages

| Package | Tests | Build |
|---|---:|---:|
| `runtime` | 44 passed, 0 skipped | PASS |
| `policy` | 24 passed, 0 skipped | PASS |
| `testkit` | 33 passed, 0 skipped | PASS |

## Frozen downstream repositories

| Repository | Revision | Baseline | Migrated | Policy | Import boundaries |
|---|---|---:|---:|---:|---:|
| `llm-router` | `6e8008a26a3d` | 343/0 | 343/0 | PASS | PASS |
| `reddit-scraper` | `c4e5b74b0356` | 52/1 | 52/1 | PASS | PASS |
| `visual-annotation` | `06e5e00bb50f` | 44/1 | 44/1 | PASS | PASS |
| `web-tools` | `b0894c8a9959` | 51/1 | 51/1 | PASS | PASS |

Total downstream result: **490 passed, 3 skipped**, unchanged before and after migration.

## Accepted clean migration contract

* Runtime remains behaviorally identical to the frozen product package.
* Policy keeps all Ternforge-specific structure, declaration, configuration, docs, e2e-slice, runnable-example, test, and workbench rules. Generic imports remain in import-linter/Ruff/Pyright.
* Policy uses PyYAML instead of a custom YAML parser because e2e_slices is an active downstream contract.
* Testkit preserves the complete public config/root/test-support surface, runtime logging, active-loop, VCR, image, path, console, and repository-specific multipart behavior.
* Consumers move atomically: dependencies, public imports, [tool.ternforge], answers provenance, managed template surface, and lockfile change together. There is no permanent py_lib_tooling compatibility package and no dual config table.
* Template-owned workflows, pre-commit, agents, scripts, setup and repository configuration come from the latest accepted hardening render; every migrated repository has only thin ci.yml/release.yml callers and zero forbidden legacy CLI/internal references.
* Only legacy py-lib-starter infrastructure that conflicts with the selected Ternforge model is removed.
