# OpenTofu provisioning results

## Result

**Architecture/design PASS. R03 and T01 PASS live. T03 repeat-bootstrap idempotency requires one final rerun. Private rulesets remain BLOCKED by the current GitHub plan.**

The configuration under `provisioning/` pins OpenTofu `1.12.0` and GitHub provider `6.6.0`. It creates one private repository, controls merge settings/topics, creates `main` from bootstrapped `dev`, switches the default branch, writes a non-secret Actions variable, optionally grants Renovate App access and defines feature-gated branch/tag rulesets.

## Live handoff-03 result

- provider init/fmt/validate: PASS;
- repository-only plan/apply: PASS;
- `sandbox-provisioned` created only by OpenTofu: PASS;
- repository initially verified private: PASS;
- post-bootstrap apply, no-drift, repeat apply and import recovery: PASS;
- cleanup/archive path: PASS;
- repeat bootstrap: FAIL because the old script rendered and committed again before its push was rejected non-fast-forward;
- credential findings in returned state/artifacts: 0.

The failed second push did not mutate the remote repository. The corrected script in commit `74413a8c31dc9315e7c8f0859af0898f43ff91fc` checks remote `refs/heads/dev` before running Copier or creating a commit. An existing `dev` branch now produces a clean exit 0.

## Required two-phase sequence

1. repository-only `tofu apply` creates `sandbox-provisioned`;
2. `bootstrap.sh` checks that remote `dev` is absent, runs Copier and pushes the first commit;
3. post-bootstrap apply creates `main`, sets `dev` as default and applies variables/App access;
4. a subsequent plan shows no drift;
5. later bootstrap runs detect remote `dev` and exit without rendering or pushing;
6. import/reconciliation uses ordinary OpenTofu state operations;
7. cleanup restores the intended private/archive state.

## Onboarding replacement map

| Current onboarding responsibility | Target owner |
|---|---|
| repository creation/visibility/description | OpenTofu `github_repository` |
| merge methods/delete branch/topics | OpenTofu |
| first project tree | Copier |
| first commit/push and remote-exists guard | 25-LOC bootstrap |
| `dev`/`main` branch creation | git bootstrap + OpenTofu `github_branch` |
| default branch | OpenTofu `github_branch_default` |
| required PR/check/no-force-push/tag policy | OpenTofu rulesets, when the plan supports them |
| Actions variables | OpenTofu |
| App repository selection | OpenTofu with separate admin identity |
| template membership | topic + `.copier-answers.yml`; no registry |
| update delivery | Renovate |
| promotion PR | thin GitHub workflow |
| validation | reusable CI and OpenTofu plan |

## Visibility deviation

After the private provisioning acceptance, the handoff agent later changed all lab repositories to public for an out-of-scope fallback test. This does not invalidate the initial private creation evidence, but the final lab state is unacceptable. Handoff-04 must remove only the recorded public-fallback rules/protections and restore all eleven repositories to private before revalidating T03.

## Secrets and state

No repository secret is modeled. Provider credentials are supplied through environment/App-token generation and are not committed variables. The only example Actions variable is non-sensitive. Handoff-03 found zero credential-like values in OpenTofu state evidence.

## Ruleset blocker

Every private ruleset attempt returned GitHub's plan-related HTTP 403. Public fallback rulesets successfully exercised the HCL shapes, tag immutability and no-drift behavior, but remain supplementary evidence only. Production must either obtain private-ruleset capability or approve and separately test a documented lower-fidelity private fallback.

## Remaining evidence

Only the corrected repeat-bootstrap guard and final private/no-drift state remain for T03. Exact instructions are in [`local-agent-handoff-04.md`](local-agent-handoff-04.md).
