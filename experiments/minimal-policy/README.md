# Minimal policy prototype

A stdlib-only checker for the organization-specific rules that are not cleanly expressed by import-linter, Ruff or Pyright.

It checks only:

- console entry points target `<package>._api.cli:*` and the function exists;
- root `__init__.py` is a declaration facade;
- literal dynamic imports cannot target `_internal`;
- Python examples begin with `# %%`;
- the minimal source/test/docs skeleton exists.

It contains no Copier wrapper, GitHub API, registry, update engine, release logic or runtime configuration. Generic import contracts remain ordinary `import-linter` configuration.

Run:

```bash
python experiments/minimal-policy/py_lib_policy.py .
python -m unittest discover experiments/minimal-policy/tests
```
