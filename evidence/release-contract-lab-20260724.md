# Release contract lab — 2026-07-24

Result: **PASS**

## Checks

- PASS — `semantic_title_reruns_on_edit`
- PASS — `squash_uses_pr_title_body`
- PASS — `docs_not_releasable`
- PASS — `renovate_fix_deps`
- PASS — `renovate_automerge`
- PASS — `patch_release_pr`
- PASS — `release_created`
- PASS — `dispatch_received`
- PASS — `labels_with_minimal_permissions`
- PASS — `repository_settings`
- PASS — `actions_defaults`
- PASS — `single_main_ruleset`
- PASS — `python_release_strategy`
- PASS — `docs_hidden_from_release`
- PASS — `release_pr_lockfile_sync`
- PASS — `official_release_pr_output`

## Repositories

- `betabitplus-template-lab/sandbox-release-contract-source-20260724-r1`
- `betabitplus-template-lab/sandbox-release-contract-consumer-20260724-r1`
- `betabitplus-template-lab/sandbox-release-contract-target-20260724-r1`

## Observed contract

- Invalid PR title failed; editing to a Conventional Commit title reran and passed the same required check.
- Squash used PR title/body; docs-only did not create a release PR.
- Renovate used `fix(deps)` for a runtime Git source and auto-merged only after CI.
- `fix(deps)` created a patch Release Please PR; release creation sent a scoped dispatch.
- Repository Actions defaults remained read-only.
- `release-type: python` updated `pyproject.toml` without generic extra-file wiring.
- A `docs:` squash commit stayed non-releasable when the Python changelog section was hidden.
- A `fix:` change created a Release PR containing the manifest, changelog, `pyproject.toml`, and `uv.lock`; `ci / required` passed.
- Lockfile synchronization used the documented Release Please `pr.headBranchName` action output, not a custom PR lookup.

## Negative probes that changed the contract

- `matchPackageNames` matched the Git repository identity, not the PEP 621 dependency name; `matchDepNames` was required for the intended runtime dependency rule.
- Release Please changed `[project].version` but not `uv.lock`; `uv sync --locked` correctly rejected the first Release PR until the release workflow synchronized the lockfile on the same PR branch.
