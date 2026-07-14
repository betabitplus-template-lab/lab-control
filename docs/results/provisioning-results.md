# OpenTofu provisioning results

## Result

**Static implementation: PASS. Live apply/no-drift: DEFERRED. Private rulesets: BLOCKED by current GitHub plan.**

The configuration under `provisioning/` pins OpenTofu `1.12.0` and GitHub provider `6.6.0`, creates one private repository, controls merge settings/topics, creates `main` from bootstrapped `dev`, switches the default branch, writes a non-secret Actions variable, optionally grants Renovate App access, and defines optional branch/tag rulesets.

## Required two-phase sequence

1. `tofu apply -var=bootstrap_complete=false` creates the empty repository.
2. `bootstrap.sh` runs Copier locally, initializes Git, commits and pushes the first `dev` branch.
3. `tofu apply -var=bootstrap_complete=true` creates `main`, sets `dev` as default, applies variables/App access and (where supported) rulesets.
4. A subsequent `tofu plan` must show no unexplained drift.

The two phases are real platform behavior, not hidden behind a Python state machine. The provider cannot set a default branch before the target ref exists.

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

## Idempotency design

- OpenTofu state owns repository settings; repeat plan is the drift signal.
- Copier bootstrap refuses a non-empty destination and a second first push.
- Repository import is supported rather than re-creating an existing repository.
- Partial creation is recovered with ordinary `tofu import`/apply and Git commands; no recovery framework is introduced.
- Cleanup defaults to archive-on-destroy; the experiment must not delete evidence unexpectedly.

## Secrets and state

No repository secret is modeled. Provider credentials are supplied from environment/App-token generation and are not variables committed to state. The only example Actions variable is non-sensitive.

## Negative result

Handoff 01 received HTTP 403 for rulesets on every private lab repository because the current account plan does not expose the feature. The HCL keeps rulesets behind an explicit feature flag defaulting to false. A production rollout must either upgrade/enable the capability or document and test a branch-protection fallback.

## Remaining live evidence

The exact handoff 02 must create `sandbox-provisioned`, execute both apply phases, capture JSON plans, re-run bootstrap/apply, test an import/partial case, and archive the repository. Until that evidence exists, the provisioning result is not marked fully accepted.
