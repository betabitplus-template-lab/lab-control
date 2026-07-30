# Grafana GitHub data source lab

## Question

Can the official Grafana GitHub data source provide useful current fleet state without a custom exporter or database, and what credential boundary actually constrains its repository access?

## Validated runtime

```text
Grafana 13.1.0, pinned by image digest
Grafana GitHub data source 2.8.0
GitHub App authentication
ephemeral GitHub-hosted runner
configuration provisioned as code
```

The final workflow commit was `a42034b41eed2b86b2a43d4fbfdbab309b218749`. Run `30584491341` completed successfully.

## Result

The data source health check returned `OK`.

| Query | Result |
|---|---:|
| Repositories | 90 rows |
| Workflows | 18 rows |
| Open Renovate pull requests | 7 rows |
| Configuration-warning issues | 0 rows |
| Releases | 0 rows |
| Workflow runs | not validated: `workflow not found` |

Zero-row issue and release responses completed without an error and therefore remain valid empty dashboard states.

Repository, workflow, pull-request, issue and release query types are sufficient for Fleet Health tables and drill-down links. Workflow-run history requires a separate successful permission/query acceptance before it can be part of the contract.

## Credential scope finding

The workflow minted a token selected to one repository, `lab-control`. The Grafana plugin nevertheless returned all 90 repositories visible to the App installation.

This is expected from the plugin authentication model: it receives the App id, installation id and private key and mints its own installation token. The workflow token's repository selection does not downscope the plugin.

Therefore the production least-privilege boundary must be:

```text
one dedicated read-only GitHub App
installed only on the managed fleet
```

It cannot be implemented by minting a narrower helper token before Grafana starts.

## Significant failed attempts

* Run `30579945130`: the existing lab App was not installed on the personal-account repositories. Personal-account acceptance could not begin.
* Run `30580534743`: the existing lab App installation did not grant `Actions: read`; requesting it was rejected.
* Run `30581427883`: plugin version `2.8.1` was absent from the Grafana catalog. Published version `2.8.0` was used.
* Run `30581878450`: GitHub.com configuration and query enum assumptions were wrong. GitHub.com requires an empty `githubUrl`; query time fields use numeric backend enums.
* Run `30582461308`: dashboard queries worked, but a table-to-SQL alert path did not produce a stable alert contract.

These attempts changed the proposed design: the GitHub plugin is retained for current-state dashboards, while critical alerts are driven by bounded operational metrics validated separately.

## Conclusion

The official data source removes the need for a custom GitHub exporter and repository-state database. It is suitable for repository, workflow, Renovate PR, configuration-warning and release views.

It is not yet accepted for personal-account production use. That final acceptance requires a dedicated read-only GitHub App installed only on selected managed repositories. `Actions: read` should be granted only if workflow-run history is required.

Machine-readable evidence is in [`grafana-github-datasource-20260730.json`](grafana-github-datasource-20260730.json).
