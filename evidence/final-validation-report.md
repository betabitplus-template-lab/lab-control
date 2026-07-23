# Ternforge final lab validation report

Date: 2026-07-23  
Scope: isolated `betabitplus-template-lab` repositories and `ternforge-lab-20260723` Scalr environment  
Baseline status: **not modified**

## Executive conclusion

The lab validation covers the complete proposed branch, promotion, publishing, dispatch, fleet-routing, GitHub App, Scalr OIDC, remote-state, RBAC, and locking contracts.

The final acceptance result is recorded in the matrix at the end of this document. Every contract is `Passed`. Negative tests are successful when the prohibited action is rejected.

## Isolation and safety

No production repository, production Scalr environment, or baseline file was changed.

All cloud-side resources created for the validation use the `ternforge-lab-*` prefix or live in the `betabitplus-template-lab` GitHub organization. All workflow credentials are short-lived GitHub OIDC or GitHub App installation tokens. No persistent Scalr token was added to GitHub secrets.

## 1. Scalr state-storage-only execution

Lab objects:

- Environment: `ternforge-lab-20260723` (`env-v0pbk6k7v6ul4m8td`)
- Workspace: `ternforge-state-lab-20260723` (`ws-v0pbk6osu69m5vfri`)

Verified API state:

- `execution-mode = local`
- `operations = false`
- `remote-backend = true`
- remote run count after OpenTofu operations: `0`
- state version created successfully
- workspace unlocked after contention tests

Important bootstrap finding: a CLI-created workspace initially used `execution-mode = remote`. State-only operation therefore requires an explicit managed `local` execution-mode attribute and a readback assertion; it must not be inferred from a CLI source type.

## 2. Scalr GitHub OIDC

Configuration:

- issuer: `https://token.actions.githubusercontent.com`
- audience: `betabitplus-template-lab`
- service account: `ternforge-lab-github-oidc`
- exact allowed repository claim: `betabitplus-template-lab/sandbox-ternforge-scalr-oidc-20260723-r1`
- assume-policy maximum session duration: `3600` seconds
- minimum requested service-account token lifetime accepted by Scalr: `600` seconds

Positive lifecycle run `29996537630` completed:

1. GitHub Actions requested an OIDC JWT.
2. Scalr exchanged it for a short-lived service-account credential.
3. OpenTofu `1.12.5` initialized the Scalr remote backend.
4. `apply` created state.
5. a second plan returned no drift.
6. state list and state pull succeeded.

Negative OIDC runs:

- wrong audience, run `29996589078`: exchange rejected
- workflow without `id-token: write`, run `29996591159`: OIDC request capability absent
- different repository, run `29996593517`: repository claim rejected

## 3. Scalr least-privilege RBAC

The remote backend requires two distinct scopes:

- workspace scope: the service account can operate on the single state workspace
- environment scope: custom role containing only `environments:read`

Run `29996924657` proved:

- allowed workspace API access succeeds
- an environment outside the granted scope is rejected

A successful provisioning exit is not sufficient acceptance evidence. During the lab, Scalr CLI returned success while relationships were not persisted. Final acceptance must read back:

- workspace execution mode and operations flag
- role permission relationships
- access-policy subject, role, and scope
- assume-policy provider and claim conditions

## 4. Scalr locking

Run `29996927248` proved:

1. one OpenTofu apply acquired the remote state lock
2. a concurrent apply failed with a state-lock error
3. the second apply succeeded after the first released the lock
4. temporary state was removed
5. the final plan returned no drift
6. no stale workspace lock remained

This confirms that `local` execution mode retains Scalr remote locking without creating Scalr remote runs.

## 5. Scalr token expiry

Final run: `30001478357`

Expected contract:

- immediate authenticated workspace read succeeds
- the same credential later fails after the requested 600-second lifetime
- the failure is an authentication response (`401` or `403`)
- elapsed time and response status are recorded in the workflow log and job summary

Observed result:

- immediate status: `200`
- expired status: `401`
- first authentication failure after: `664` seconds

## 6. Protected branch contract

Final contract repository: `sandbox-ternforge-final-contract-20260723-r1`

### `dev`

- pull request required
- only squash merge allowed
- literal required context: `ci / required`
- expected check source: GitHub Actions App integration ID `15368`
- direct push rejected
- deletion rejected
- non-fast-forward update rejected

### `main`

- pull request required
- only merge commit allowed
- literal required contexts: `ci / required` and `promotion / required`
- expected check source: GitHub Actions App integration ID `15368`
- direct push rejected
- deletion rejected
- non-fast-forward update rejected

### Release tags

For `refs/tags/v*`:

- deletion rejected
- non-fast-forward update rejected
- no bypass actors configured

Live tests confirmed:

- merge commit into `dev` rejected; squash accepted
- squash and rebase into `main` rejected; merge commit accepted
- direct pushes into `dev` and `main` rejected with `GH013`

Required status contexts are literal check-run names. The stable workflow contract is created by explicit job names such as `name: ci / required`, not by assuming GitHub will concatenate workflow and job names.

## 7. Promotion guard

The promotion workflow verifies:

1. source repository equals base repository
2. source branch is exactly `dev`
3. PR head SHA equals the current `refs/heads/dev` SHA
4. the prospective merge tree of `main + dev` equals the current `dev` tree

Validated cases:

- normal no-sync promotion: passed repeatedly
- source branch other than `dev`: run `29998289790` failed and PR remained blocked
- stale `dev` head: run `29998364612` failed
- current synchronized `dev` head: run `29998382370` passed
- true content conflict: GitHub marked the PR `DIRTY` and did not create a merge ref
- a second promotion after an earlier merge commit succeeded without merging `main` back into `dev`

## 8. Release publisher

The publisher verifies before creating or accepting a release:

- current `main` commit has two parents
- promoted SHA is `main^2`
- `tree(main) == tree(main^2)`
- project version equals the Release Please manifest version
- tag points to the promoted SHA
- GitHub Release target points to the promoted SHA

Run `29998051274` created `v0.3.0` from GitHub Actions. Run `29998084474` immediately repeated the operation successfully without mutation, proving idempotency.

For `v0.3.0`:

- tag SHA equals promoted SHA
- Release target equals promoted SHA
- generated notes include the real feature PR
- promotion and release-preparation PRs are excluded by labels

Tag immutability tests:

- deletion returned a repository-rule violation
- force update returned a repository-rule violation

Wrong-tag fail-closed test:

- `v0.4.0` was deliberately created on an incorrect old SHA
- after a valid `0.4.0` promotion, publisher run `29998222773` failed
- publisher did not rewrite the immutable tag

## 9. Cross-repository dispatch

Source: `lab-control`  
Target: `sandbox-ternforge-dispatch-target-20260723-r1`

Run `29998914668` proved:

- minted GitHub App token reports exactly one accessible repository
- dispatch to the source repository is rejected
- dispatch to the target repository succeeds

Target run `29998924315` validated the exact payload:

- event type: `ternforge-lab-release`
- source: `sandbox-ternforge-final-contract-20260723-r1`
- version: `0.3.0`

## 10. Renovate shard token boundary

Run `29999042911` used `actions/create-github-app-token` `v3.2.0` pinned to commit `bcd2ba49218906704ab6c1aa796996da409d3eb1`.

Verified:

- installation-token readback contains exactly `sandbox-renovate-shard-01`
- a temporary Git branch can be created and removed inside that repository
- creating a Git branch in `sandbox-renovate-shard-02` is rejected

Public repository metadata reads and public issue creation are not valid authorization probes. Repository-scope acceptance must use installation-repository readback and a contents-write operation.

The action reports that `app-id` is deprecated in favor of `client-id`; final implementation should use the current input name.

## 11. Deterministic fleet routing

Reproducible evidence:

- `experiments/renovate_shard_model.py`
- `evidence/renovate-shards.json`
- Actions run `29998637015`

Assignment algorithm:

`SHA-256(full_repository_name)[0:8] mod shard_count`

Results:

| Fleet | Shards/jobs | Minimum repos/shard | Maximum repos/shard |
|---:|---:|---:|---:|
| 1,000 repositories | 8 | 107 | 140 |
| 5,000 repositories | 32 | 132 | 189 |

Both scenarios satisfy:

- fewer than 256 GitHub matrix jobs
- fewer than 500 repositories per GitHub App token
- deterministic assignment independent of inventory order
- every repository assigned exactly once

Inventory validation rejects:

- duplicate repositories
- unknown profiles
- unknown update sources
- profiles with no update sources

## 12. Final acceptance matrix

A negative scenario is marked passed when the prohibited operation was rejected.

| Contract | Result |
|---|---|
| State-only local Scalr execution | Passed |
| No Scalr remote runs | Passed |
| Scalr remote state lifecycle | Passed |
| Scalr state locking and recovery | Passed |
| GitHub OIDC positive exchange | Passed |
| Wrong OIDC audience rejection | Passed |
| Missing `id-token: write` rejection | Passed |
| Wrong repository claim rejection | Passed |
| Workspace/environment RBAC boundary | Passed |
| 600-second token expiry | Passed |
| Squash-only `dev` | Passed |
| Merge-only `main` | Passed |
| Direct-push rejection | Passed |
| Literal required check contexts | Passed |
| Check source pinned to GitHub Actions App | Passed |
| Exact `dev` source guard | Passed |
| Stale-head rejection | Passed |
| Prospective merge-tree guard | Passed |
| No-sync repeated promotions | Passed |
| Publisher exact promoted SHA | Passed |
| Publisher idempotency | Passed |
| Generated-notes filtering | Passed |
| Immutable release tags | Passed |
| Wrong existing tag fail-closed | Passed |
| Repository-scoped dispatch token | Passed |
| Repository-scoped Renovate token | Passed |
| Deterministic 1,000/5,000-repository routing | Passed |

## Baseline decision

No baseline change was made during validation. Baseline editing is permitted only after every row in the final acceptance matrix is `Passed` and the committed machine-readable evidence matches this report.
