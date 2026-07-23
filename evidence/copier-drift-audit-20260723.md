# Copier drift audit lab — 23 July 2026

## Result

```text
PASS
```

The experiment used Copier `9.16.0` and uv `0.8.17` against two private repositories in `betabitplus-template-lab`.

| Checkout | Local drift | Git name-status |
| --- | --- | --- |
| `clean-state` | no | `—` |
| `dev` | yes | `A	CREATE_ONCE.txt; A	deleted-managed.txt; M	managed.txt` |

## Assertions

- PASS — `clean_recopy_has_empty_diff`
- PASS — `drift_paths_match_expected`
- PASS — `modified_skip_if_exists_is_preserved`
- PASS — `unrelated_user_file_is_ignored`
- PASS — `answers_file_is_stable`
- PASS — `clean_head_unchanged`
- PASS — `drift_head_unchanged`
- PASS — `remote_dev_sha_unchanged`
- PASS — `version_drift_reported_for_clean_checkout`
- PASS — `version_drift_reported_for_drift_checkout`

## Contract demonstrated

```text
fleet target
→ disposable shallow checkout
→ copier check-update
→ copier recopy --vcs-ref=:current: --defaults --overwrite --skip-tasks
→ git add -N .
→ git diff --name-status / git diff --binary
```

The clean checkout produced no local diff while still reporting that template `v1.1.0` exists above recorded `v1.0.0`. The divergent checkout reported only the expected template-footprint deviations: one modified managed file and two recreated missing template files. The existing modified `_skip_if_exists` README and unrelated committed user file were not reported. Local and remote commit SHAs remained unchanged.

Machine-readable evidence: `evidence/copier-drift-audit-20260723.json`.
