# Local agent handoff 03: revalidate remediated failures only

## Objective

Revalidate only the handoff-02 failures corrected after the live run. Do not repeat phases already marked `PASS` or `NEGATIVE_PASS` unless a corrected item explicitly depends on them. Do not redesign the architecture.

Source implementation:

- repository: `betabitplus-template-lab/lab-control`;
- branch: `experiment/final-platform-20260714`;
- draft PR: `lab-control#9`;
- template compatibility PR: `python-lib#19`;
- nested fixture PR: `sandbox-workspace#8`.

Read [`handoff-02-integration-results.md`](handoff-02-integration-results.md) before execution.

## Absolute safety

1. The active credential must have `push=false` and `admin=false` for every `betabitplus/*` repository, or be unable to see them.
2. Every mutation target must begin with `betabitplus-template-lab/`.
3. Do not query production through Renovate autodiscovery, OpenTofu targets or write APIs.
4. Automerge remains false.
5. Do not merge or modify `sandbox-python-lib#3`.
6. Do not rewrite/delete tags `python-lib@v0.1.0` through `v0.4.1`, C1/C2/C3, first-stage evidence or historical releases.
7. Never print private keys, tokens, signed JWTs, authorization headers or credential-bearing URLs.
8. Keep provider tokens in environment variables only; inspect state/artifacts for secrets before returning them.
9. Stop before every live command if its resolved repository list contains anything outside the explicit allowlist below.

## Approved repository allowlist

- `betabitplus-template-lab/lab-control`
- `betabitplus-template-lab/automation`
- `betabitplus-template-lab/python-lib`
- `betabitplus-template-lab/sandbox-process`
- `betabitplus-template-lab/sandbox-provisioned`
- `betabitplus-template-lab/sandbox-workspace`

Do not mutate any other repository in this handoff.

## Pinned tools

Use and record immutable references:

- OpenTofu `1.12.0`;
- GitHub provider `integrations/github 6.6.0`;
- actionlint `1.7.12`;
- zizmor `1.27.0`;
- Copier `9.16.0`;
- Renovate `43.262.4`, image digest `sha256:2c2f2dc64e0c4ef0d4c9f5795877004ee9667eb3d3f1125ebb1dc503aeeae8fe`;
- uv `0.8.17` or the exact newer version already selected in the lab evidence, recorded explicitly.

## 1. Fetch and static revalidation — S03, S04, D03, D05

Check out the current PR #9 head, not the old handoff-02 SHA.

Run:

```bash
actionlint tooling/direct-quality.yml
actionlint automation-repository/.github/workflows/ensure-promotion-pr.yml
actionlint automation-repository/.github/workflows/template-acceptance.yml
actionlint release-please/release-please.yml
zizmor --pedantic --offline .
python3 experiments/minimal-policy/tests/test_policy.py
python3 -m py_compile experiments/minimal-policy/py_lib_policy.py
```

Run the corrected policy against the exact generated baseline used by handoff-02:

```text
betabitplus-template-lab/sandbox-process@d594c0dd80908f89bc5a534681f27765fb985c4b
```

Expected: exit `0`. Preserve the old legacy-checker result for parity; do not modify the historical commit.

Run the exact direct packaging workflow commands on a clean checkout/fixture:

- `uv sync --frozen --all-groups`;
- `uv build`;
- pinned `uvx` twine check;
- pinned `uvx` check-wheel-contents;
- `uv run check-manifest --ignore .copier-answers.yml`;
- isolated wheel and sdist install/import/console smoke;
- pytest.

Record individual exit codes and artifact SHA-256 values. Expected S03, D03 and D05: `PASS`.

For OpenTofu:

```bash
cd provisioning
tofu init -upgrade=false
tofu fmt -check
tofu validate -json
```

Expected S04: `PASS` with provider 6.6.0 and no unsupported schema arguments.

## 2. Publish corrected automation source

Publish the corrected files from `automation-repository/` to a new reviewable commit in `automation`. Do not rewrite `automation@v0.1.0`; create a new immutable tag only after the corrected reusable workflows pass. Record the commit and tag.

The final downstream callers must use an exact commit SHA, not the new tag.

## 3. Promotion workflow — P04

Update only `sandbox-process` with the corrected promotion caller/workflow pinned to the exact corrected automation SHA.

Trigger a safe commit to `dev` or rerun with an existing ahead state. Verify:

- the workflow succeeds without checkout credentials;
- GitHub compare API reports `main...dev` correctly;
- exactly one open `dev → main` PR exists;
- a second trigger creates no duplicate;
- automerge remains false;
- the promotion PR remains unmerged for this handoff unless a merge is strictly required by a later approved acceptance item.

Expected P04: `PASS`.

## 4. OpenTofu full two-phase flow — R03, T01, T03

Only OpenTofu may create `betabitplus-template-lab/sandbox-provisioned`. Do not create it manually.

Use the corrected `provisioning/` configuration unchanged except declared variable values/IDs. Keep `enable_rulesets=false` because the private-plan 403 is already proven.

Execute and preserve redacted plans:

1. repository-only plan/apply;
2. verify private repository, topics, merge settings and no unexpected resources;
3. run `provisioning/bootstrap.sh` with Copier and create `dev` plus `main` baseline;
4. post-bootstrap plan/apply for default branch, Actions variable and approved App installation access;
5. second plan with exit code `0`/no changes;
6. repeat apply and bootstrap to prove idempotency;
7. one import or partial-state recovery exercise;
8. archive/destroy cleanup according to `archive_on_destroy`, without deleting evidence.

Inspect state JSON and artifacts for credential-like values before returning them. Expected R03, T01 and T03: `PASS`.

P06/T04/L05 remain `BLOCKED` unless the GitHub plan has changed. Do not emulate rulesets with an undocumented fallback.

## 5. Private Copier acceptance and release workflow — L04

Use the corrected private authentication path from `automation-repository/.github/workflows/template-acceptance.yml`.

Verify on Linux, macOS and Windows:

- recursive private components checkout;
- Copier's independent temporary clone can read the private components submodule;
- no credential is persisted in Git config/artifacts/logs;
- the acceptance workflow succeeds through the reusable call.

Then exercise the corrected prepared Release Please workflow on one new safe patch line after v0.4.1. Do not rewrite old tags. Verify:

- acceptance is a required dependency;
- the release App token is repository-scoped;
- the tag/release target equals the current `main` SHA using the GitHub API guard;
- exact automation SHA is used;
- automerge remains false.

Expected L04: `PASS`. Record PR, run, commit, tag and release IDs.

## 6. Legacy-answer Copier update plus lock — K03

Use draft `python-lib#19` as the compatibility fix. First run template acceptance on its head. When green, merge it through ordinary review and create a new immutable patch tag; do not move existing tags.

Then rerun the previously failing old-answer update in `sandbox-process`:

- start from the same old answer shape that omits hidden `template_profile`;
- update to the new template tag through Renovate/Copier;
- allow exactly `uv lock` as the post-upgrade command;
- require `.copier-answers.yml`, generated files and `uv.lock` in the same PR;
- run `uv lock --check` and full CI;
- rerun Renovate and prove no duplicate/change after the first PR stabilizes;
- preserve unrelated lock entries and private Git authentication;
- automerge remains false.

Expected K03: `PASS`.

## 7. Nested workspace acceptance — K05

Run CI on `sandbox-workspace#8`. Expected behavior:

- exactly two nested answer files;
- both `_commit` values are valid `vX.Y.Z` tags;
- both values are equal;
- package-root and conflict checks remain active.

When green, merge the fixture fix through normal review. Rebase/recreate the earlier nested update PR if necessary and prove both lock files pass idempotently. Expected K05: `PASS`.

## 8. PEP 508 Git dependencies — K06

Publish the corrected `renovate/presets/downstream.json5` to `automation` and pin the consumer to the new exact automation commit.

Use a temporary lab branch/fixture value one valid production tag behind the current `py-lib-starter` tag for only:

```text
py-lib-runtime @ git+https://github.com/betabitplus/py-lib-starter.git@vX.Y.Z#subdirectory=packages/py-lib-runtime
```

Run Renovate extract/lookup/full dry phases first. Verify the custom regex manager extracts:

- dependency name `py-lib-runtime`;
- package `betabitplus/py-lib-starter`;
- GitHub tags datasource;
- current semver without the `v` prefix;
- no unrelated PEP 508 Git URL.

Run one reviewed live update PR with `uv.lock`, CI and automerge false. Repeat once for `py-lib-tooling` or prove both are independently extracted in the same fixture. Rerun Renovate and prove idempotency. Expected K06: `PASS`.

Do not target any production repository; reading public production tags as a datasource is allowed, writing is forbidden.

## 9. Final audit and return bundle

Return:

```text
handoff-03/
  report.md
  report.json
  command-log.redacted.txt
  static/
  automation/
  process/
  provisioning/
  release/
  lock-refresh/
  tooling/
  security/
```

`report.json` must list exactly these revalidated IDs:

```text
S03 S04 R03 P04 T01 T03 L04 K03 K05 K06 D03 D05
```

For each use only `PASS`, `NEGATIVE_PASS`, `BLOCKED` or `FAIL`, with exact repository/PR/run/commit/tag/release/artifact IDs and evidence paths. Also include unchanged blocked statuses P06/T04/L05, every lab mutation, every cleanup action, production mutation audit, automerge audit, current state of `sandbox-python-lib#3`, and a credential scan summary.

Do not mark a corrected item `PASS` based only on static inspection when its section requires a live operation.
