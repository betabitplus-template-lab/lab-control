# Copier create-once deletion lab

## Question

Which native Copier 9.16.0 rule expresses create-once ownership while preserving intentional deletion during normal updates and the read-only `recopy` drift audit?

## Compared models

Two otherwise identical versioned templates were exercised from `v0.1.0` to `v0.2.0`:

1. `README.md` declared in `_skip_if_exists`;
2. `README.md` excluded during update through a Jinja-templated `_exclude` pattern using `_copier_operation`.

For both consumers, `README.md` was deleted and committed before the template update. The template changed both `README.md` and a separately managed file.

A third disposable consumer verified the audit path. Its template used the same `_exclude` rule with an additional explicit `ternforge_recopy_audit=true` data flag. The consumer contained a deleted create-once README and committed drift in a managed file before `copier recopy --vcs-ref=:current:`.

## Result

All assertions passed.

| Scenario | Deleted README | Managed state | Answers |
|---|---|---|---|
| Update with `_skip_if_exists` | Recreated as untracked new template content | Updated | Advanced to `v0.2.0` |
| Update with operation-aware `_exclude` | Remained deleted | Updated | Advanced to `v0.2.0` |
| Audit `recopy` with explicit data flag | Remained deleted | Managed drift restored and visible as the only diff | Unchanged |

`_skip_if_exists` protects a destination only while that path exists. It does not represent a deletion tombstone. A templated `_exclude` rule prevents the path from being rendered during updates, whether the destination currently exists or not. Because Copier treats `recopy` as a copy operation, the read-only audit passes an explicit data flag that activates the same exclusion without changing recorded answers.

## Conclusion

Ternforge create-once paths whose intentional deletion must persist use operation-aware `_exclude`, not `_skip_if_exists`. The read-only drift audit passes `ternforge_recopy_audit=true` so the same user-owned paths remain outside the audit footprint while managed drift remains visible.

The experiment used no tasks, migrations, extensions or `--trust`. Machine-readable observations are in [`copier-deleted-create-once-20260729.json`](copier-deleted-create-once-20260729.json), and the reproducible test is [`experiments/copier_deleted_create_once_lab.py`](../experiments/copier_deleted_create_once_lab.py).
