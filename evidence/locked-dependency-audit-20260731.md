# Locked dependency vulnerability audit lab

Date: 2026-07-31
Outcome: **passed**

## Question

Can a Python repository enforce a fail-closed vulnerability gate directly from its frozen `uv.lock`, limited to runtime dependencies, without product-specific Python tooling?

## Environment

- Python: `3.10.16`
- Platform: `macOS-26.5.2-arm64-arm-64bit`
- uv: `uv 0.12.0 (b88d7c5c4 2026-07-28 aarch64-apple-darwin)`
- pip-audit: `pip-audit 2.10.1`
- vulnerable fixture: `setuptools==65.5.0`

## Results

| Assertion | Result |
|---|---|
| `native_runtime_vulnerability_blocks` | PASS |
| `native_no_dev_excludes_dev_only_vulnerability` | PASS |
| `native_default_includes_dev_vulnerability` | PASS |
| `native_exact_ignore_restores_success` | PASS |
| `native_command_is_still_experimental` | PASS |
| `pip_audit_exported_runtime_vulnerability_blocks` | PASS |
| `pip_audit_export_excludes_dev_only_vulnerability` | PASS |
| `pip_audit_exact_ignore_restores_success` | PASS |
| `pip_audit_runs_from_locked_dev_environment` | PASS |
| `runtime_export_is_fully_pinned` | PASS |

Native `uv audit` vulnerability IDs: `GHSA-5rjg-fvgr-3xxf, GHSA-cx63-2mw6-8hw5, GHSA-h35f-9h28-mq5c, GHSA-r9hx-vwmv-q579, PYSEC-2022-43012, PYSEC-2025-49, PYSEC-2026-1918, PYSEC-2026-3447`

`pip-audit` vulnerability IDs: `PYSEC-2022-43012, PYSEC-2025-49, PYSEC-2026-1918, PYSEC-2026-3447`

## Conclusion

The production-ready path is the stable `pip-audit 2.10.1` CLI:

```bash
uv export --frozen --no-dev --no-emit-project --output-file runtime-requirements.txt
uv run --frozen --no-sync pip-audit --requirement runtime-requirements.txt --no-deps --disable-pip
```

It works as one ordinary development dependency plus direct CI commands. No custom production Python script or wrapper package is required.

Native `uv audit --frozen --no-dev` also enforces the gate correctly, but `uv 0.12.0` still labels the command and its JSON schema experimental. It should be reconsidered after Astral stabilizes the interface.
