# OpenTofu provisioning results

## Result

**Architecture/design PASS. Handoff-02 repository-only apply FAIL before write because of one provider-schema mismatch. Corrected implementation awaits handoff-03 live apply/no-drift. Private rulesets remain BLOCKED by the current GitHub plan.**

The configuration under `provisioning/` pins OpenTofu `1.12.0` and GitHub provider `6.6.0`. It creates one private repository, controls merge settings/topics, creates `main` from bootstrapped `dev`, switches the default branch, writes a non-secret Actions variable, optionally grants Renovate App access and defines feature-gated branch/tag rulesets.

## Handoff-02 result

OpenTofu correctly stopped before creating `sandbox-provisioned`. Provider 6.6.0 rejected `allowed_merge_methods` inside two `github_repository_ruleset.rules.pull_request` blocks. No manual repository substitute was created, so the failed apply produced no partial lab mutation.

The unsupported fields were removed in `lab-control#9` commit `7f241a8d0e56b408a2a70f0085e6d307c1acbf42`. Squash-only behavior is still declared by repository merge settings (`allow_merge_commit=false`, `allow_rebase_merge=false`, `allow_squash_merge=true`). The ruleset continues to require a PR, review, resolved threads, no deletion/force-push and the selected status check where the GitHub plan supports it.

## Required two-phase sequence

1. repository-only `tofu apply` creates `sandbox-provisioned`;
2. `bootstrap.sh` runs Copier locally, initializes Git, commits and pushes the first `dev` branch;
3. post-bootstrap apply creates `main`, sets `dev` as default, applies variables/App access and optional rulesets;
4. a subsequent `tofu plan` must show no unexplained drift;
5. repeat apply/bootstrap and one import/partial-state recovery case prove idempotency;
6. cleanup archives rather than unexpectedly deleting evidence.

The two phases are explicit platform behavior, not hidden behind a Python state machine. The provider cannot set a default branch before the target ref exists.

## Onboarding replacement map

| Current onboarding responsibility | Target owner |
|---|---|
| repository creation/visibility/description | OpenTofu `github_repository` |
| merge methods/delete branch/topics | OpenTofu |
| first project tree | Copier |
| first commit/push | 15-LOC bootstrap |
| `dev`/`main` branch creation | git bootstrap + OpenTofu `github_branch` |
| default branch | OpenTofu `github_branch_default` |
| required PR/check/no-force-push/tag policy | OpenTofu rulesets, when plan supports them |
| Actions variables | OpenTofu |
| App repository selection | OpenTofu with separate admin identity |
| template membership | topic + `.copier-answers.yml`; no registry |
| update delivery | Renovate |
| promotion PR | thin GitHub workflow |
| validation | reusable CI and OpenTofu plan |

## Secrets and state

No repository secret is modeled. Provider credentials are supplied through environment/App-token generation and are not committed variables. The only example Actions variable is non-sensitive. Handoff-03 must inspect state JSON and returned artifacts for credential-like values before reporting success.

## Ruleset blocker

Every private ruleset attempt returned GitHub's plan-related HTTP 403. `enable_rulesets` remains explicit and defaults false. The experiment does not silently claim branch-protection fallback parity. Production must either obtain private-ruleset capability or approve and separately test a documented lower-fidelity fallback.

## Remaining evidence

Handoff-03 must run provider validation, repository-only apply, Copier bootstrap, post-bootstrap apply, clean second plan, repeat/idempotency, one import/partial-state recovery and archive cleanup. Until those live steps pass, R03/T01/T03 remain revalidation-required rather than PASS.
