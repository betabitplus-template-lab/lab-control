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

## GitHub Actions validation

- Workflow run: `30025437084`
- Job: `89268585229`
- Head SHA: `77587a7957a69d1b8bc2559b6b81eae29904194d`
- Conclusion: `success`
- Exact token repository set: template + consumer sandbox only
- Token permission: `contents: read`
- Attempted branch creation: denied
- Artifact id: `8571049711`
- Artifact digest: `sha256:087c7f7a4c722783e57c2e1d8c9e95ef23dbffafca681103d728219856fd979f`
- Raw JSON SHA-256: `9f579ecea59cc0a89d36631d0cb48fbf9166094edfcfa983700a55847bbaeca2`
- Raw Markdown SHA-256: `8664735d1fa283796a7cf138353b8a0c434ad6281a1765dee06ce8e3bfde9fd7`

The GitHub-hosted run reproduced the local result with current `client-id` input and `actions/upload-artifact` v7.0.1.
