# Private uv and lock-maintenance validation — 2026-07-24

## Scope

This bounded follow-up validates only the two gaps not already closed by earlier lab evidence:

1. native Renovate `uv.lock` maintenance without a custom `uv lock` task;
2. private Git dependency lookup and lock regeneration with separate target-write and source-read credentials.

Earlier K06 evidence already proved private Git authentication, grouped Git dependency updates, lock regeneration and duplicate-free reruns. The final Renovate token-boundary lab already proved exact target repository scoping. Those broader experiments were not repeated.

## Fixtures

- private source: `betabitplus-template-lab/sandbox-private-uv-source-20260724-r1`;
- private consumer: `betabitplus-template-lab/sandbox-private-uv-consumer-20260724-r1`;
- pinned Renovate: `43.262.4`;
- consumer `[tool.uv].required-version`: `==0.8.17`;
- target credential: exact consumer repository, `contents: write`, `pull_requests: write`, `issues: write`;
- dependency credential: exact source repository, `contents: read` only.

Both runs verified exact installation repository sets, denied cross-scope reads and denied writes with the dependency credential.

## Native lock maintenance

- run: `30053952781` — PASS;
- PR: consumer `#2`;
- changed files: only `uv.lock`;
- result: `packaging 24.0 → 25.0` within the existing `>=24,<26` constraint;
- Renovate executed native `uv lock --upgrade`;
- Renovate installed `uv 0.8.17` from `[tool.uv].required-version`;
- the private source at `v0.1.0` was fetched successfully by the child `uv` process;
- no custom post-upgrade task, lock script or custom manager was used.

The consumer retains the official `:maintainLockFilesMonthly` preset. The live run used a lab-only schedule override so the monthly mechanism could be executed immediately; it does not alter the production monthly decision.

## Private Git tag update

- source release: `v0.2.0`, commit `db2e2e2d9c1792b62837f603d6d71a62e1520e34`;
- run: `30054199900` — PASS;
- PR: consumer `#3`;
- changed files: `pyproject.toml`, `uv.lock`;
- tag: `v0.1.0 → v0.2.0`;
- lock source: exact commit changed to `db2e2e2d9c1792b62837f603d6d71a62e1520e34`;
- the existing PR was reused on the confirming run; no duplicate PR was created;
- no credential-bearing URL was written to `pyproject.toml`, `uv.lock` or the retained PR diff.

The dependency credential was configured for both Renovate source lookup and Git HTTPS authentication inherited by the child `uv` process. The target credential could not read the private source, and the dependency credential could neither read the target nor write to the source.

## Important correction found by the lab

A target token with only `contents: write` and `pull_requests: write` failed during Renovate GitHub initialization because Renovate queried repository issues. The target credential therefore also needs `issues: write`. This is also required for Renovate's normal configuration-warning issue behavior.

The private source credential remains `contents: read` only.

## Verdict

PASS with one baseline clarification required:

- keep monthly native lock maintenance, exact uv selection and separate private-source credential as written;
- explicitly include `issues: write` in the exact-target Renovate platform credential;
- do not add a custom lock script, custom package manager, PAT, credential URL or persistent credential wrapper.
