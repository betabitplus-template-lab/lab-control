# Handoff-04 integration results

Date: 2026-07-16  
Bundle SHA-256: `ffa83d8f2d252d5a42be4dda64d3185b30dd253c83a84683096b3eb59bbdc136`  
Executed source: `lab-control@a1b1555239681195028f8e7eb38a48f47880c191`

## Decision

**Three of the four final functional checks passed. K06 remains a real implementation failure, not an access or plan limitation.**

| ID | Status | Accepted evidence |
|---|---|---|
| P04 | PASS | corrected promotion workflow succeeded twice against the same `dev → main` PR, run `29422268451`, no duplicate and no automerge |
| T03 | PASS | repeat bootstrap exited 0 without changing refs; subsequent OpenTofu plan exited 0 |
| K03 | PASS | component/template release `v0.4.3`, release `354495776`; downstream PR `sandbox-process#10` contains Copier changes and `uv.lock`; CI run `29424887496` passed |
| K06 | FAIL | extraction/lookup passed, but the live run lost the literal `v` during replacement and created separate update branches instead of one grouped update |

No item in this four-ID set is blocked by permissions or the GitHub plan.

## Safety

- production mutations: `0`;
- visibility mutations: `0`;
- automerge enabled: `false`;
- `sandbox-python-lib#3`: open, unmerged and unchanged at `82542cf617b2d55b2b609f5f53654e16e44f36bb`;
- new or rotated credentials: `0`;
- credential/private-key/header/credential-URL findings: `0`;
- temporary `TEMPLATE_READ_TOKEN` used for K03 was deleted and never logged.

The K06 live run unintentionally pruned stale Renovate PR branches. The agent restored the recorded refs, reopened PRs `#4`, `#5` and `#10`, rebuilt PR `#10` from current `dev`, and reran its CI successfully. This cleanup is included in the mutation audit and does not invalidate K03.

## Private/public capability

Visibility was intentionally left unchanged. All eleven lab repositories are currently public.

Previously established results remain authoritative:

- private ordinary Git/Copier/workflow/Renovate/release flows: `PASS`;
- private branch/tag rulesets on the current plan: `BLOCKED` with HTTP 403;
- equivalent public ruleset fallback: `PASS`.

No additional private/public test is required for K06.

## Static checks

- actionlint 1.7.12: exit `0`;
- `bash -n provisioning/bootstrap.sh`: exit `0`;
- zizmor 1.27.0 pedantic/offline: exit `12`, with one low `undocumented-permissions` finding and no medium/high findings.

The low finding referred to the promotion workflow's `pull-requests: write`. The permission is necessary and was already explained by a preceding comment; the comment has now been moved inline in commit `415487ffeb5beba6b0c622f96033421328a32c75` so the audit can associate the documentation with the permission.

## K06 root cause and correction

The returned live logs identify two deterministic configuration defects:

1. `currentValue` captured `v0.32.3`, while `extractVersionTemplate` normalized the new release to `0.32.4`. Default replacement therefore wrote `@0.32.4`, which the literal `@v...` regex could not re-extract.
2. The group rule used `matchPackageNames` with dependency aliases. The actual `packageName` for both records is `betabitplus/py-lib-starter`; the aliases are their `depName` values.

Corrections now in review:

- the literal `v` is outside the `currentValue` capture, so only `0.32.3 → 0.32.4` is replaced and `@v...` remains valid;
- grouping uses `matchDepNames: [py-lib-runtime, py-lib-tooling]`;
- `minimumGroupSize: 2` prevents a partial shared-source update;
- a Node regression test verifies extraction, replacement, re-extraction and grouping configuration.

Implementation:

- `lab-control#9`: commits `88e756cdead0ffb751c55af50483b6fd48faaf9f` and `0dbdc7448f201e129670768b4e6d5b2d231e23a2`;
- reviewable automation publication: `automation#1`, commit `1554ac4295daa4c75d983ddab0fca1442b33e675`, automerge disabled.

Renovate's official configuration model distinguishes `depName` from `packageName`; `matchDepNames` is specifically the package-rule matcher for dependency aliases. The regex manager also replaces the captured `currentValue`, so leaving the syntactic `v` outside that capture preserves it during updates.

## Final gate

Only one live check remains: rerun K06 against `automation@1554ac4295daa4c75d983ddab0fca1442b33e675` and require one grouped PR containing both refs plus `uv.lock`, green CI, no duplicate on rerun and automerge false.

No new credential, private/public rerun, OpenTofu rerun, release rerun or K03 rerun is required.
