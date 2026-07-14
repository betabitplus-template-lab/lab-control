# Local agent handoff 02: execute only remaining live lab evidence

## Objective

Execute the exact live operations that the primary environment cannot perform. All implementation/configuration is already authored in [lab-control#9](https://github.com/betabitplus-template-lab/lab-control/pull/9). Do not redesign it. Return evidence; make only the lab changes listed here.

## Absolute safety

1. Use a credential that has `push=false` and `admin=false` for every `betabitplus/*` production repository, or cannot see them.
2. Every target must start with `betabitplus-template-lab/`.
3. Production writes, Renovate discovery and OpenTofu targets are forbidden.
4. Automerge remains false. Do not merge `sandbox-python-lib#3` or rewrite tags `v0.1.0`–`v0.3.0`.
5. Mask all tokens. Do not persist private keys or provider tokens in files/state/artifacts.
6. Stop before a live phase whenever its dry output contains a repository outside the expected allowlist.

## 1. Fetch implementation

Check out `betabitplus-template-lab/lab-control` branch `experiment/final-platform-20260714`. Verify the PR head and run the static suite documented in `docs/results/final-experiment-results.md`.

Install/pin OpenTofu `1.12.0`, a digest-pinned Renovate image matching the experiment pin, actionlint and zizmor. Record versions and immutable references.

## 2. Create only the three approved repositories

Create no others:

- `betabitplus-template-lab/automation` (permanent);
- `betabitplus-template-lab/sandbox-process` (experiment);
- `betabitplus-template-lab/sandbox-provisioned` (OpenTofu target; let OpenTofu create it, not manual API).

Publish `automation-repository/` to `automation`. Keep it private. Enable private Actions access for repositories in the organization. Record repository SHA and access-setting response.

## 3. Reusable workflow acceptance

Update the caller in `sandbox-python-platform#3` to the exact `automation` commit SHA, without merging the PR. Verify Linux/macOS, inherited secret without disclosure, read-only caller permission, intentional failure propagation, cancellation, tagged/exact refs and keep exact SHA selected. Run actionlint and zizmor and return raw outputs.

## 4. Renovate private presets and topic discovery

Publish `renovate/presets/` into `automation/renovate/presets/`. Use existing repositories for managed, untagged, managed-disabled and template cases. Run explicit allowlist, read-only discovery, org filter, topic filter, extract, lookup, full, one reviewed live run and an idempotency rerun. No production repository may appear and automerge remains false.

## 5. `dev → main` process

Configure only `sandbox-process`: Copier project, `dev` default, `main` promotion, Renovate to `dev`, protections/checks and no automerge. Produce one safe update PR, merge after CI, verify exactly one promotion PR and prove rerun idempotency plus a blocking failure/conflict.

## 6. OpenTofu provisioning

Use `provisioning/` unchanged except values/IDs. Supply provider token through environment only. Execute repository-only apply, Copier bootstrap, post-bootstrap apply, no-drift plan, repeat apply/bootstrap, one import/partial recovery case and archive cleanup. Keep rulesets disabled after recording the current-plan 403.

## 7. Release Please

Use one existing template and a new `v0.4.x` line. Do not alter old tags. Publish the prepared configuration; exercise conventional commit, release PR, acceptance gate, merge, tag/release, exact-main-SHA checks and Renovate tag discovery. If tag rulesets remain unavailable, record BLOCKED honestly.

## 8. Lock refresh

Create one real template dependency change. Verify Copier update plus exact allowlisted `uv lock` in the same PR, `uv lock --check`, idempotency, stable unrelated entries and private Git auth. Repeat one nested workspace dependency change. Update `py-lib-runtime` as a normal dependency PR.

## 9. Component wiring edges

On new branches only, test new file/no implicit output, explicit wiring, broken symlink negative PR, one rename and optional generated audit artifact. Do not modify C1/C2/C3 or existing evidence.

## 10. Private access negative test

Create a temporary lab-only credential with template/downstream read and no components read; record expected redacted failure. Add components read and record success. Revoke it afterward.

## 11. Direct-tool fixture parity

Against frozen good/bad fixtures, run old wrapper/checker, direct commands and minimal policy. Produce rule-by-rule parity JSON and wheel/sdist smoke. Do not add compatibility wrappers merely to preserve names.

## Required return

Return `handoff-02/report.md`, `report.json`, redacted command log and evidence directories for Renovate, workflows, process, provisioning, release, lock refresh, wiring, private access, tooling parity and security. Every acceptance item must be `PASS`, `NEGATIVE_PASS`, `BLOCKED` or `FAIL` with exact repository/PR/run/commit/tag/artifact IDs, production mutation audit and every lab mutation.
