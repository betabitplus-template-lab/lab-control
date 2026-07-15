# Reusable workflows results

## Result

**PASS for private cross-repository reuse, exact-SHA selection, secret inheritance, failure propagation and cancellation. One corrected private Copier clone path requires handoff-03 revalidation.**

The final private implementation was published in `betabitplus-template-lab/automation` at commit `a5cd8112c8e8b221dceb397c1e882a9a25148b86`, tag `v0.1.0`. Organization access for private callers was enabled. The downstream caller remains [sandbox-python-platform#3](https://github.com/betabitplus-template-lab/sandbox-python-platform/pull/3) with automerge disabled.

## Caller reduction

The caller contains only trigger, read permission, immutable reusable-workflow ref, inputs and inherited secrets. The reusable implementation owns OS matrices, stable check names and validation behavior. Workflow implementation changes require only a reviewable exact-SHA ref bump; template-generated product/config changes still use Copier.

## Live acceptance

| Acceptance | Result | Evidence |
|---|---|---|
| Linux/macOS execution, inherited secret presence, read-only permissions | PASS | run `29375576270` |
| intentional failure propagation | NEGATIVE_PASS | run `29375625874`, conclusion failure |
| cancellation propagation | NEGATIVE_PASS | run `29375658789`, conclusion cancelled |
| tagged `automation@v0.1.0` ref | PASS | run `29375727768` |
| final exact 40-character automation SHA | PASS | run `29375763651` |
| actionlint and zizmor review of reusable set | PASS | handoff-02 workflow evidence |
| automerge | disabled | PR metadata audit |

This supersedes the earlier `lab-control` pre-job failure `29371633018`: that run correctly exposed that private source-workflow sharing is an administrative setting, not repository content. After publishing the dedicated `automation` repository and enabling organization access, the private call worked.

## Private Copier authentication finding

The reusable template acceptance workflow initially authenticated `actions/checkout` but Copier performed an independent temporary Git clone. That clone could not read the private components submodule. The corrected workflow sets an ephemeral process-environment Git URL rewrite from the masked read token on Linux/macOS/Windows, keeps `persist-credentials:false`, and does not write credentials to repository config or artifacts.

The corrected path is in `lab-control#9` commit `51dcb45cd8c06ff0e2d1540df095b07f88b0f124`. Live cross-platform revalidation is assigned to handoff-03 and is the only remaining reusable-template acceptance gap.

## Updating the reusable ref

Renovate can detect reusable workflow `uses:` refs, but the main Renovate App intentionally has no Workflows write permission. The selected model uses `automation/.github/workflows/secure-workflow-update.yml` with a separate selected-repository App.

The updater validates one repository, one workflow path and two exact SHAs, changes exactly one occurrence, proves no other file changed and opens a PR to `dev`. It never merges. This preserves least privilege and reviewability at the cost of a bounded 99-line optional workflow.
