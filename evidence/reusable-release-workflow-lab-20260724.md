# Reusable release workflow lab — 2026-07-24

Result: **PASS**

## Checks

- PASS — `caller_pushes_to_main`
- PASS — `provider_uses_workflow_call`
- PASS — `caller_pins_provider_sha`
- PASS — `named_credential_passed`
- PASS — `client_id_used`
- PASS — `client_id_from_repository_variable`
- PASS — `exact_repository_scope_verified`

## Repositories

- `betabitplus-template-lab/sandbox-release-workflow-provider-20260724-r1`
- `betabitplus-template-lab/sandbox-release-workflow-caller-20260724-r1`

## Observed contract

- A local caller triggered on `push` to `main` and `workflow_dispatch`.
- The caller invoked a cross-repository reusable workflow pinned to an exact commit SHA.
- The caller passed one named credential and a repository variable containing the App Client ID.
- `actions/create-github-app-token` used `client-id`, minted a token, and verified an exact one-repository installation scope.
