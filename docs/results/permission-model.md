# Permission model

## Principles

- selected-repository GitHub App installations;
- short-lived installation tokens instead of persistent PATs;
- no production access from lab identities;
- no Workflows permission on the main Renovate App;
- no identity may both publish workflow changes and merge them without review;
- template consumers need read access to both template and private components repositories.

## Actors

| Actor | Repository access | Permissions | Prohibited |
|---|---|---|---|
| Template consumer (human/CI) | selected templates + components | Contents read | writes, administration, secrets |
| Main Renovate App | selected managed templates/downstreams | Metadata read; Contents read/write; Pull requests read/write; Issues read/write | Workflows, Administration, Secrets, merge bypass |
| Template acceptance CI | current template + components | Contents read; Actions normal execution | persistent token, repository settings writes |
| Release App | selected template repositories only | Contents write; Pull requests/Issues write; Metadata read | downstream access, administration except explicit tag bypass identity |
| Workflow publisher App | selected downstream repositories only | Contents write + Workflows write; Pull requests write | merge, administration, broad organization install |
| OpenTofu provisioning identity | management repository and explicitly provisioned targets | Administration/settings, Contents bootstrap as needed, Actions variables, App-installation access | product secrets in state, broad day-to-day use |
| Human maintainer | normal team role | review/merge under rules | direct protected-branch/tag mutation |
| Optional fleet reporter | topic-discovered repositories | Metadata/PR/check read | all writes |

## Current lab proof

Handoff 01 rotated the Renovate App key and proved that its installation token sees exactly eight lab repositories. It has Contents, Issues and Pull requests write but no Workflows or Administration permission. Production push/admin is false.

Current logs/artifacts were scanned with zero credential findings. Real tokens/private keys must never be committed or uploaded as artifacts; workflows use masking and installation-token generation.

## Private template boundary

A Copier operation against a private template containing a private submodule needs read access to:

1. the final template repository;
2. the components repository at the committed gitlink;
3. the downstream repository when updating/pushing a PR.

A credential lacking components read must fail early during clone/submodule checkout. This is acceptable for a single production organization if team/App installation membership is managed centrally. It is not acceptable for anonymous/external consumers without a separate distribution mechanism.

## Workflow update recommendation

Choose **Variant B**:

- Renovate detects/report workflow dependency changes but does not mutate workflow files.
- A separate trusted updater receives old/new 40-character SHAs, validates one `.github/workflows/*.yml|yaml` path, mints a token for exactly one repository, changes exactly one occurrence and opens a PR to `dev`.
- Required review and CI remain mandatory; the updater never merges.

Variant A (Workflows write on Renovate) is simpler but couples high-frequency dependency automation to a permission capable of modifying executable CI. It is not recommended unless the separate updater becomes materially more complex than the present 99-line workflow.

## OpenTofu authentication caveat

The provider's `github_app_installation_repository` resource is incompatible with GitHub App installation authentication. App repository-selection changes therefore require a separate organization-administrative identity. Keep that identity outside routine CI and use it only during reviewed provisioning.
