# Local agent handoff 04: restore privacy and close the final four failures

## Objective

Restore the isolated lab to its required private shape, then revalidate only the four handoff-03 failures corrected in the current experiment branch:

```text
P04 T03 K03 K06
```

Do not repeat already accepted phases except where one of these four items requires a dependency. Do not redesign the architecture.

Source:

- repository: `betabitplus-template-lab/lab-control`;
- branch: `experiment/final-platform-20260714`;
- draft PR: `lab-control#9`;
- evidence interpretation: `docs/results/handoff-03-integration-results.md`;
- component patch: `experiments/remediation/k03-components.patch`.

## Absolute safety

1. No write may target `betabitplus/*`.
2. Production baseline remains `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`.
3. Production mutation audit must run before and after all work.
4. Autmerge remains disabled.
5. Do not merge or modify `sandbox-python-lib#3`.
6. Do not rewrite/delete historical tags, releases, C1/C2/C3 or prior evidence.
7. Never print tokens, private keys, authorization headers, signed JWTs or credential-bearing URLs.
8. Use environment-only credentials and redact command logs.
9. Stop before a command if its resolved write target is outside the allowlists below.
10. Do not run the public fallback again.

## Visibility restoration — mandatory first phase

Handoff-03 changed all eleven lab repositories to public outside the bounded instruction. Before functional work:

1. Capture current repository visibility, archive/default-branch state, rulesets and branch protections.
2. Preserve the existing public-fallback evidence.
3. Remove only the public-fallback controls after verifying their exact repository/name/target:
   - `python-lib` ruleset `18987692`, `immutable-v0.4-release-tags`;
   - `sandbox-provisioned` rulesets `18987811`, `18987816`, `18987819`;
   - public fallback branch protections on `sandbox-process/dev` and `sandbox-process/main`.
4. Change all eleven repositories below to `private`.
5. Verify `private=true` and `visibility=private` for every repository.
6. Verify no unexpected rule/protection was deleted.
7. Recheck private P06/T04/L05. Keep them `BLOCKED` if GitHub still returns the plan-related HTTP 403.
8. Do not substitute public behavior for the private result.

Repositories to restore:

```text
automation
components
lab-control
python-internal-package
python-lib
python-starter-platform
sandbox-process
sandbox-provisioned
sandbox-python-lib
sandbox-python-platform
sandbox-workspace
```

If an archived repository cannot change visibility, unarchive only for the visibility operation and restore its intended archive state afterward. Record every such mutation.

## Functional write allowlist

After visibility restoration, functional writes are limited to:

```text
betabitplus-template-lab/lab-control
betabitplus-template-lab/automation
betabitplus-template-lab/components
betabitplus-template-lab/python-lib
betabitplus-template-lab/sandbox-process
betabitplus-template-lab/sandbox-provisioned
```

## Pinned tools

Record exact versions/references:

- OpenTofu `1.12.0`;
- GitHub provider `integrations/github 6.6.0`;
- actionlint `1.7.12`;
- zizmor `1.27.0`;
- Copier `9.16.0`;
- Renovate `43.262.4`;
- Renovate image digest `sha256:2c2f2dc64e0c4ef0d4c9f5795877004ee9667eb3d3f1125ebb1dc503aeeae8fe`;
- the exact uv version used.

## 1. Static/security revalidation

Check out the current PR #9 head, not the handoff-03 source SHA.

Run actionlint over every workflow under:

```text
.github/workflows/
automation-repository/.github/workflows/
release-please/
tooling/
```

Run:

```bash
zizmor --pedantic --offline .
bash -n provisioning/bootstrap.sh
python3 experiments/minimal-policy/tests/test_policy.py
python3 -m py_compile experiments/minimal-policy/py_lib_policy.py
```

The branch contains hardening for inherited workflows: exact action SHAs, selected-repository App tokens, explicit App permissions, `persist-credentials:false`, temporary askpass, concurrency and named jobs.

Do not claim whole-repository zizmor success unless its exit code is zero. If any residual remains, return exact file/line/audit and do not weaken the checker.

## 2. P04 — promotion controller

Publish the corrected `automation-repository/.github/workflows/ensure-promotion-pr.yml` to a new reviewable `automation` commit. Do not rewrite an existing tag. Pin the downstream caller to the exact automation commit SHA.

On `sandbox-process`:

1. Ensure `dev` is ahead of `main`.
2. Keep exactly one open `dev → main` PR (`#2` may be reused).
3. Trigger the corrected workflow.
4. Require a successful run.
5. Verify the compare API reports the correct ahead count.
6. Verify both `gh pr list` and `gh pr create` are explicitly scoped with `--repo`.
7. Trigger again and prove no duplicate PR is created.
8. Verify automerge remains false and the promotion PR remains unmerged.

Expected: P04 `PASS`.

## 3. T03 — idempotent bootstrap

Use the corrected `provisioning/bootstrap.sh` from PR #9.

The first bootstrap and OpenTofu repository creation are already accepted under R03/T01. Revalidate only the failed repeat behavior against `sandbox-provisioned`:

1. Capture remote `dev` and `main` SHAs.
2. Run the corrected bootstrap with the same repository/template inputs.
3. It must detect remote `refs/heads/dev` before rendering or committing, print the already-initialized result, and exit 0.
4. Run it a second time; the result must be identical.
5. Prove no local generated commit was pushed and remote branch SHAs are unchanged.
6. Import/reconcile the repository with OpenTofu as needed.
7. Require a no-drift plan.
8. Restore the intended private/archive state during cleanup.

Expected: T03 `PASS`.

## 4. K03 — legacy answers, template update and exact lock refresh

Apply `experiments/remediation/k03-components.patch` exactly to `components` on a reviewable branch.

The patch must:

- remove the obsolete `py-lib-template-check` pre-push hook that assumes `_copier_answers.yml`;
- change the generated Pyright constraint from `>=1.1.410` to `>=1.1.411`, providing a deterministic lock-metadata change;
- make no unrelated component changes.

Then:

1. Open a components PR, run available validation, review and merge normally.
2. Update only the `python-lib` `_components` gitlink to the exact merged components commit.
3. Run private template acceptance.
4. Merge through review and publish the next immutable patch release after `v0.4.2`; do not move old tags.
5. Recreate or update the legacy-answer Renovate/Copier PR in `sandbox-process`.
6. The same PR must contain:
   - `.copier-answers.yml`;
   - `.pre-commit-config.yaml`;
   - `pyproject.toml`;
   - `uv.lock`.
7. The only post-upgrade command is exact `uv lock`.
8. Run `uv lock --check`, full CI and the full pre-push hook set.
9. Verify no command references `py-lib-template-check`.
10. Rerun Renovate and prove idempotency/no duplicate.
11. Keep automerge false.

Expected: K03 `PASS`.

## 5. K06 — grouped PEP 508 Git package update

Publish the current corrected downstream preset from PR #9 to a new exact `automation` commit. It contains two literal regex managers:

- `py-lib-runtime`;
- `py-lib-tooling`.

They are independently extracted but grouped into one update because both packages currently use the same `betabitplus/py-lib-starter` root tag.

Use a temporary `sandbox-process` branch/fixture where both refs are the same valid production tag behind `v0.32.4`. Do not create an invalid mixed-ref lock state.

1. Run Renovate extract/lookup/full dry phases.
2. Verify two distinct dependencies, exact package name `betabitplus/py-lib-starter`, GitHub-tags datasource, semver extraction without the leading `v`, and no unrelated PEP 508 match.
3. Verify there is no `depName mismatch`.
4. Run one reviewed live update.
5. Require one grouped PR updating both refs to the same current root tag and regenerating `uv.lock`.
6. Run full CI and `uv lock --check`.
7. Rerun Renovate and prove no duplicate/change.
8. Clean up only the temporary fixture branch after preserving evidence.
9. Keep automerge false.

Expected: K06 `PASS`.

## 6. Final audits

Repeat:

- visibility audit: all eleven lab repositories private;
- production baseline/dev/tag audit: zero mutations;
- automerge audit across every lab PR;
- `sandbox-python-lib#3` state/head audit;
- credential scan over logs, artifacts and OpenTofu state;
- old tag/release immutability audit;
- temporary branch/key/ruleset/protection cleanup audit.

P06/T04/L05 remain `BLOCKED` unless private endpoints genuinely work after restoration. Public-fallback PASS evidence remains supplementary and must not replace them.

## Return bundle

Return one ZIP containing:

```text
handoff-04/
  report.md
  report.json
  command-log.redacted.txt
  visibility/
  static/
  automation/
  promotion/
  provisioning/
  components/
  template-release/
  lock-refresh/
  renovate/
  security/
```

`report.json` must contain:

```text
functional_acceptance:
  P04
  T03
  K03
  K06
```

Each functional ID uses exactly one status: `PASS`, `NEGATIVE_PASS`, `BLOCKED` or `FAIL`.

Also include separate fields for:

- all eleven before/after visibility records;
- deleted public-fallback rule/protection IDs;
- unchanged private blockers P06/T04/L05;
- actionlint and zizmor exit codes;
- every repository/PR/run/commit/tag/release/artifact ID;
- every lab mutation and cleanup;
- production mutations;
- automerge audit;
- `sandbox-python-lib#3`;
- credential scan.

Do not mark a functional item `PASS` from static inspection when its section requires live execution.
