# OpenTofu repository provisioning experiment

The configuration deliberately exposes the unavoidable two-phase sequence:

1. `tofu apply -var=post_bootstrap=false` creates an empty private repository and settings/topics.
2. `bootstrap.sh` runs Copier and pushes the first commit to `dev`.
3. `tofu apply -var=post_bootstrap=true` creates `main` from `dev`, fixes the default branch, adds variables/App access and applies rulesets when the GitHub plan supports them.
4. `tofu plan -detailed-exitcode -var=post_bootstrap=true` must return `0`.

`enable_rulesets` defaults to false because handoff-01 proved that rulesets on these private lab repositories return HTTP 403 on the current GitHub plan. Production must enable the flag only where the plan supports private rulesets.

No GitHub secret is declared. Provider authentication comes from the process environment and is not modeled as state.
