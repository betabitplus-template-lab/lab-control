# Product Capability Parity Experiment

This experiment validates the complete legacy-to-Ternforge product capability
migration without modifying any source repository.

Run from the `lab-control` repository root with the frozen repositories checked
out as siblings:

```bash
uv run --python 3.13 --with PyYAML python \
  experiments/product_capability_parity_lab.py prepare \
  --legacy ../py-lib-starter \
  --runtime ../runtime-prototype \
  --policy ../policy-prototype \
  --testkit ../testkit-prototype \
  --inventory experiments/product-capability-parity/capability_matrix.json \
  --output evidence/product-capability-parity-20260801
```

The experiment inputs are committed with the runner:

* `capability_matrix.json` — the 73-row unresolved capability inventory passed
  to `prepare`;
* `legacy-inventory.json` — the frozen structural inventory from which the
  capability review was derived;
* `inventory_extract.py` — the reproducible extractor for that structural
  snapshot.

Regenerate the structural inventory when the sibling repositories are checked
out at the recorded revisions:

```bash
uv run --python 3.13 python experiments/product-capability-parity/inventory_extract.py \
  --workspace .. \
  --output /tmp/ternforge-legacy-inventory.json
```

For each frozen consumer, record the unchanged baseline and then validate the
atomic migration:

```bash
uv run --python 3.13 --with PyYAML python \
  experiments/product_capability_parity_lab.py baseline \
  --output evidence/product-capability-parity-20260801 \
  --consumer ../consumer-llm-router \
  --name llm-router

uv run --python 3.13 --with PyYAML python \
  experiments/product_capability_parity_lab.py migrate \
  --output evidence/product-capability-parity-20260801 \
  --consumer ../consumer-llm-router \
  --name llm-router
```

Repeat the two commands for:

* `reddit-scraper`;
* `visual-annotation`;
* `web-tools`.

Finalize only after all four repositories have both results:

```bash
uv run --python 3.13 --with PyYAML python \
  experiments/product_capability_parity_lab.py finalize \
  --output evidence/product-capability-parity-20260801
```

The migration phase uses the latest accepted template hardening render by
default:

```text
evidence/template-system-hardening-20260801/renders/python-default
```

It replaces the complete template-owned workflow, pre-commit, agent, setup,
script, and repository-configuration surface before checking for forbidden
legacy CLI or internal references across the whole migrated repository.

The final evidence consists of:

* `migration-matrix.json` — one of three allowed dispositions for all 73
  capabilities;
* `result.json` — machine-readable package and downstream acceptance;
* `report.md` — concise human-readable closure.

The runner deletes all experimental package and consumer copies during
finalization. It never writes to the frozen inputs.
