# Ternforge template-system hardening

Status: **PASS**

## Scope

* one released components repository;
* minimal infrastructure final template;
* full Python-library final template;
* Vendir committed snapshots with explicit legal-path filtering;
* explicit Jinja wrappers and pyproject fragments;
* Copier 9.17.0 fresh/update lifecycle and upstream edge cases;
* full Python product checks.

## Result

```text
component source files        171
infra snapshot files          15
Python snapshot files         166
Python output owners          163
infra rendered files          17
Python rendered files         163
Python product checks         32
Copier negative file mode     100644
Copier controlled file mode   100755
components v0.1.0 SHA         02e2e49b51918dff0dd5cdd145162d93fabd285c
components v0.2.0 SHA         17563ad0d02cebdcfb0e903541d0f421c89076cd
components v0.3.0 SHA         3a5465a217f8b29535a5b73063363f0374a0021e
```

Validated:

* infrastructure fresh output is exact and contains no Python/product leakage;
* each final template snapshots only its declared component paths through built-in Vendir `includePaths`;
* explicit `legalPaths: []` prevents root LICENSE/NOTICE files from bypassing selective snapshots;
* a Python-only component release changes only the infra Vendir declaration and lock, not its component files or render;
* componentized Python render matches the EXP-0031 product candidate outside platform provenance files;
* default and custom Python renders work through the actual component wrappers;
* `_components`, `.git`, assembler, manifests, `WIRING.json`, tasks, migrations and extensions do not reach consumers;
* a Python-only component release changes Python output and leaves infra output unchanged;
* a shared base component release changes exactly `.editorconfig` in both products;
* Copier updates preserve modified/deleted README and user-owned Python source;
* a guarded conditional `_exclude` remains safe when a new question is absent from old answers;
* Copier 9.17.0 reproduces the upstream new-executable limitation under `core.fileMode=false`;
* controlled updates with explicit `core.fileMode=true` preserve new executable files as `100755`;
* Vendir lock SHAs match released component commits and repeated sync is clean;
* the componentized Python render passes the full product verification suite.

## Checks

```text
component_leakage_zero: PASS
component_snapshots_filtered: PASS
component_snapshots_match_wrappers_exactly: PASS
copier_conditional_exclude_guarded: PASS
copier_controlled_executable_mode: PASS
copier_user_ownership_preserved: PASS
custom_python_render: PASS
full_python_product_checks: PASS
infra_exact_output: PASS
legacy_platform_mechanisms_zero: PASS
python_only_update_isolated: PASS
python_product_parity: PASS
shared_update_exact: PASS
vendir_legal_paths_disabled: PASS
vendir_lock_exact: PASS
vendir_repeat_sync_clean: PASS
```
