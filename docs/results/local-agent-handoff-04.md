# Local agent handoff 04: final unresolved live checks only

## Objective

Run only the remaining live checks that cannot be completed through the GitHub connector alone:

```text
P04 T03 K03 K06
```

Do not repeat acceptance items already marked PASS. Do not redesign the architecture.

Source:

- repository: `betabitplus-template-lab/lab-control`;
- branch: `experiment/final-platform-20260714`;
- draft PR: `lab-control#9`;
- interpretation of the previous run: `docs/results/handoff-03-integration-results.md`;
- K03 component patch: `experiments/remediation/k03-components.patch`.

## Access and visibility policy

Use the existing working credential. Do **not** create, rotate or replace GitHub App keys, PATs, SSH keys, deploy keys or Apps merely to reduce permissions.

Broad access inside the isolated lab is acceptable for this final test. The only hard access boundary is:

- writes are allowed only in `betabitplus-template-lab/*`;
- no write may target `betabitplus/*`;
- do not run Renovate, OpenTofu or mutation scripts against production repositories.

Do not change repository visibility as part of this handoff. Preserve the existing evidence:

- private repositories: all supported private flows passed except private rulesets, which are blocked by the current GitHub plan;
- public repositories: the equivalent ruleset shapes were exercised successfully;
- report both facts separately in the final report.

## Safety

1. Run a production mutation audit before and after the work.
2. Autmerge remains disabled.
3. Do not merge or modify `sandbox-python-lib#3`.
4. Do not rewrite or delete historical tags, releases, C1/C2/C3 or prior evidence.
5. Never print tokens, private keys, authorization headers, signed JWTs or credential-bearing URLs.
6. Keep credentials in environment variables and redact logs.
7. Stop before a command if its resolved write target is outside `betabitplus-template-lab/*`.

## Current implementation

Check out the current head of `experiment/final-platform-20260714`, not the old handoff-03 SHA.

The relevant corrections are already committed:

- P04: all `gh pr` operations are explicitly scoped with `--repo "$GITHUB_REPOSITORY"`;
- T03: `provisioning/bootstrap.sh` checks remote `dev` before rendering or committing and exits successfully when the repository is already initialized;
- K03: `experiments/remediation/k03-components.patch` removes the obsolete `py-lib-template-check` pre-push hook and changes a deterministic dependency constraint so `uv lock` must update in the same Copier PR;
- K06: runtime and tooling use separate literal Renovate managers, explicit dependency names and one grouped shared-root-tag update.

## Static check of the current head

Run only these static checks because the workflows changed after handoff-03:

```bash
actionlint $(find .github/workflows automation-repository/.github/workflows release-please tooling -type f \( -name '*.yml' -o -name '*.yaml' \))
zizmor --pedantic --offline .
bash -n provisioning/bootstrap.sh
```

Record exact exit codes. Do not weaken or suppress a finding merely to obtain a zero exit code.

## P04 — corrected promotion controller

Publish the current corrected `automation-repository/.github/workflows/ensure-promotion-pr.yml` to a reviewable commit in `automation`. Do not rewrite an existing tag. Pin the caller to the exact automation commit SHA.

On `sandbox-process`:

1. ensure `dev` is ahead of `main`;
2. keep exactly one open `dev → main` PR (`#2` may be reused);
3. trigger the corrected workflow;
4. require a successful run;
5. verify the compare API reports the correct ahead count;
6. trigger it a second time and prove no duplicate promotion PR is created;
7. verify automerge is false.

Expected result: `P04 = PASS`.

## T03 — bootstrap idempotency only

Use the already provisioned `sandbox-provisioned` repository and the current `provisioning/bootstrap.sh`.

Do not repeat the complete OpenTofu experiment. Only prove the corrected second-run behavior:

1. confirm remote `refs/heads/dev` already exists;
2. run `bootstrap.sh` again with the same repository/template/ref inputs;
3. require exit code `0`;
4. verify no new commit, branch or rejected push was produced;
5. run one OpenTofu plan and require no unexplained changes;
6. preserve the existing archive state after the check.

Expected result: `T03 = PASS`.

## K03 — legacy-answer Copier update with a real lock change

Use the current `python-lib@v0.4.2` line and the patch in `experiments/remediation/k03-components.patch`.

1. Apply the patch to a reviewable branch in `components`.
2. Validate the component/template acceptance path.
3. Publish the resulting template change through an ordinary reviewable lab PR and a new immutable patch tag. Do not move existing tags.
4. Start from the same old downstream answer shape that omits hidden `template_profile`.
5. Let Renovate/Copier create the downstream update PR.
6. Require the same PR to contain:
   - `.copier-answers.yml`;
   - generated template changes;
   - `uv.lock` changed by the deterministic dependency constraint;
7. run `uv lock --check` and the ordinary CI;
8. rerun Renovate and prove no duplicate or additional change;
9. verify the obsolete `py-lib-template-check` hook is absent;
10. verify automerge is false.

Expected result: `K03 = PASS`.

## K06 — grouped PEP 508 Git dependency update

Publish the current `renovate/presets/downstream.json5` to `automation` and pin the consumer to the exact automation commit.

Use an existing lab downstream fixture. Set both Git dependencies one valid root tag behind the current production source tag:

```text
py-lib-runtime @ git+https://github.com/betabitplus/py-lib-starter.git@vX.Y.Z#subdirectory=packages/py-lib-runtime
py-lib-tooling @ git+https://github.com/betabitplus/py-lib-starter.git@vX.Y.Z#subdirectory=packages/py-lib-tooling
```

Reading production tags as a datasource is allowed. Writing to production is forbidden.

Run Renovate `extract`, `lookup` and `full` dry phases, then one reviewed live run. Verify:

1. runtime is extracted as `py-lib-runtime`;
2. tooling is extracted as `py-lib-tooling`;
3. both use package `betabitplus/py-lib-starter` and GitHub tags datasource;
4. no unrelated PEP 508 URL is extracted;
5. both updates are grouped into one PR because they share one root tag stream;
6. both refs move to the same tag;
7. `uv.lock` is included and `uv lock --check` passes;
8. CI passes;
9. automerge is false;
10. a second Renovate run creates no duplicate or additional change.

Expected result: `K06 = PASS`.

## Final report

Return one ZIP containing:

```text
handoff-04/
  report.md
  report.json
  command-log.redacted.txt
  static/
  p04/
  t03/
  k03/
  k06/
  security/
```

`report.json` must contain exactly these functional IDs:

```text
P04 T03 K03 K06
```

For each use only `PASS`, `NEGATIVE_PASS`, `BLOCKED` or `FAIL` and include exact repository, PR, workflow run, commit, tag, release and artifact identifiers plus evidence paths.

Also include:

- current visibility of every lab repository, without changing it;
- the already established capability statement: private rulesets `BLOCKED` by plan, public ruleset fallback `PASS`;
- all lab mutations and cleanup actions performed in this handoff;
- production mutation audit before and after;
- automerge audit;
- current state of `sandbox-python-lib#3`;
- credential scan summary;
- actionlint and zizmor exit codes.

Do not mark an item PASS from static inspection when its section requires a live run.