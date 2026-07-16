# Final local-agent task: K06 live rerun only

## Objective

Validate the corrected grouped PEP 508 Git dependency update. Do not repeat P04, T03, K03, OpenTofu, releases, private/public rulesets or other accepted tests.

## Source

- `betabitplus-template-lab/lab-control` branch `experiment/final-platform-20260714`;
- main draft PR `lab-control#9`;
- reviewable preset publication: `betabitplus-template-lab/automation#1`;
- exact preset commit: `1554ac4295daa4c75d983ddab0fca1442b33e675`.

## Access

Use the existing working credential. Do not create or rotate Apps, PATs, SSH keys, deploy keys or private keys.

Writes are allowed only inside `betabitplus-template-lab/*`. Production `betabitplus/*` is read-only and may only supply tag data. Do not change repository visibility. Do not enable automerge. Do not modify `sandbox-python-lib#3`.

## Static regression

From the current lab-control head run:

```bash
node experiments/renovate-pep508/test_downstream_preset.mjs
```

Also rerun:

```bash
actionlint $(find .github/workflows automation-repository/.github/workflows release-please tooling -type f \( -name '*.yml' -o -name '*.yaml' \))
zizmor --pedantic --offline .
```

Record exact exit codes and findings. Do not suppress findings.

## K06 live validation

Use `sandbox-process` or an equivalent existing lab fixture containing both dependencies at `v0.32.3`:

```text
py-lib-runtime @ git+https://github.com/betabitplus/py-lib-starter.git@v0.32.3#subdirectory=packages/py-lib-runtime
py-lib-tooling @ git+https://github.com/betabitplus/py-lib-starter.git@v0.32.3#subdirectory=packages/py-lib-tooling
```

Pin the consumer preset to exact commit:

```text
1554ac4295daa4c75d983ddab0fca1442b33e675
```

Prevent unrelated stale-branch cleanup in the operator configuration (`pruneStaleBranches=false` or an equivalent bounded repository/branch policy).

Run Renovate 43.262.4 through extract, lookup, full dry-run and one reviewed live run. Require:

1. runtime is extracted as `depName=py-lib-runtime`;
2. tooling is extracted as `depName=py-lib-tooling`;
3. both use `packageName=betabitplus/py-lib-starter` and datasource `github-tags`;
4. current values are `0.32.3` while the literal file syntax remains `@v0.32.3`;
5. no unrelated PEP 508 URL is extracted;
6. exactly one branch/PR is created with group slug `shared-python-git-packages`;
7. both file refs become `@v0.32.4` and are re-extracted successfully;
8. `uv.lock` is included and `uv lock --check` passes;
9. CI passes;
10. automerge is false;
11. a second Renovate run creates no duplicate or additional change;
12. no pre-existing unrelated Renovate PR or branch is closed, deleted or modified.

Expected result: `K06 = PASS`.

## Safety audit

Record before/after production mutation snapshots, current lab visibility without changing it, automerge audit, `sandbox-python-lib#3` state and credential scan. Expected production mutations, visibility mutations, credential creation/rotation and automerge enables are all zero.

## Return

Return one ZIP containing:

```text
k06-final/
  report.md
  report.json
  command-log.redacted.txt
  static/
  k06/
  security/
```

`report.json` must contain exactly one functional ID: `K06`, with status `PASS`, `NEGATIVE_PASS`, `BLOCKED` or `FAIL` and exact repo, PR, branch, commit, run, job and evidence identifiers.
