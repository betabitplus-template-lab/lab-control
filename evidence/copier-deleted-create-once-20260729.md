# Copier create-once deletion lab

## Question

Which native Copier 9.16.0 rule expresses create-once ownership while preserving an intentional deletion during later updates?

## Compared models

Two otherwise identical versioned templates were exercised from `v0.1.0` to `v0.2.0`:

1. `README.md` declared in `_skip_if_exists`;
2. `README.md` excluded only during update through a Jinja-templated `_exclude` pattern using `_copier_operation`.

For both consumers, `README.md` was deleted and committed before the template update. The template changed both `README.md` and a separately managed file.

## Result

All assertions passed.

| Model | Deleted README after update | Managed file update | Conflicts or reject files |
|---|---|---|---|
| `_skip_if_exists` | Recreated with the new template content | Applied | None |
| `_exclude` when `_copier_operation == 'update'` | Remained deleted | Applied | None |

`_skip_if_exists` protects a destination only while that path exists. It does not represent a deletion tombstone. A templated `_exclude` rule prevents the path from being rendered during updates, whether the destination currently exists or not.

## Conclusion

Ternforge create-once paths whose intentional deletion must persist use operation-aware `_exclude`, not `_skip_if_exists`.

The experiment used no tasks, migrations, extensions or `--trust`. Machine-readable observations are in [`copier-deleted-create-once-20260729.json`](copier-deleted-create-once-20260729.json), and the reproducible test is [`experiments/copier_deleted_create_once_lab.py`](../experiments/copier_deleted_create_once_lab.py).
