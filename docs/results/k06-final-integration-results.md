# K06 final integration result

Date: 2026-07-16  
Archive SHA-256: `7a32d84eb1e11468bd9d4de49be6857e509c47d1a99e8f7e1e26e9f7e63ad811`  
Tested source: `betabitplus-template-lab/lab-control@db66b9aa6062d316548ef85cb0a7daa24303ce01`

## Decision

`K06 = PASS`.

This closes the last unresolved functional item from handoff-04. No further local-agent acceptance run is required.

## Accepted live path

The corrected Renovate preset was consumed from:

- repository: `betabitplus-template-lab/automation`;
- draft PR: `#1`;
- exact commit: `1554ac4295daa4c75d983ddab0fca1442b33e675`.

The consumer fixture was `betabitplus-template-lab/sandbox-process@1a512157bcf29e205812c416d84a653f52aa9254` on `dev`.

Renovate 43.262.4 created exactly one grouped update:

- PR: `sandbox-process#11`;
- branch: `renovate-lab/shared-python-git-packages`;
- head: `23180206f1df692ca3d0627edc69c86aadd19454`;
- base: `dev`;
- state: open and mergeable;
- automerge: disabled.

The PR atomically changes:

```text
py-lib-runtime: v0.32.3 -> v0.32.4
py-lib-tooling: v0.32.3 -> v0.32.4
```

Both records use source package `betabitplus/py-lib-starter` and datasource `github-tags`. The literal `@v...` syntax is preserved before and after replacement.

Changed files are exactly:

- `pyproject.toml`;
- `uv.lock`.

`uv lock --check` exited `0`. An updated-branch Renovate extraction found both dependencies at numeric `currentValue=0.32.4` with the literal `v` still present in source text and no extraction errors.

## CI and idempotency

Workflow run `29487631571` completed successfully at `23180206f1df692ca3d0627edc69c86aadd19454`:

- job `87585796258`: required reusable smoke, success;
- job `87585796277`: representative macOS smoke, success.

A second live Renovate run exited `0` and preserved:

- grouped PR count: `1`;
- duplicate grouped PRs: `0`;
- grouped branch head: unchanged;
- additional changes: `0`.

Unrelated Renovate PRs and branches were unchanged. `pruneStaleBranches=false` was enforced for the live operator run.

## Static checks

- Node downstream-preset regression test: exit `0`;
- actionlint 1.7.12: exit `0`;
- `zizmor 1.27.0 --pedantic --offline .`: exit `0`, findings `0`.

This also closes the final workflow-security rerun requested after handoff-04.

## Safety

- production mutations: `0`;
- production repository/dev/tag snapshots: unchanged;
- repository visibility mutations: `0`;
- automerge enables: `0`;
- credentials or keys created/rotated: `0`;
- credential scan findings: `0`;
- `sandbox-python-lib#3`: open, unmerged, unchanged at `82542cf617b2d55b2b609f5f53654e16e44f36bb`.

The agent temporarily disabled `enforce_admins` on the lab-only `sandbox-process/dev` branch solely to push the controlled fixture commit and restored it to `true`. No other protection setting changed.

## Independent GitHub verification

The integration review independently confirmed:

- `sandbox-process#11` is one open, mergeable PR with head `23180206f1df692ca3d0627edc69c86aadd19454`;
- its diff updates both Git refs to `v0.32.4` and regenerates the matching lock entries;
- workflow run `29487631571` has both recorded jobs completed successfully;
- `automation#1` remains open/draft at exact commit `1554ac4295daa4c75d983ddab0fca1442b33e675`;
- `sandbox-python-lib#3` remains open at its protected historical head.

## Final interpretation

The isolated implementation is now **functionally complete**. The architecture remains **CONDITIONAL GO** for production because private branch/tag rulesets are unavailable on the current GitHub plan. The equivalent public ruleset configurations already passed, so the remaining item is a rollout capability/operating decision, not an untested code path.
