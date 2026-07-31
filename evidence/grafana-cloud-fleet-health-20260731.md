# Grafana Cloud Fleet Health end-to-end lab

## Question

Can the proposed minimal Fleet Health architecture work end to end in managed Grafana Cloud without a custom exporter, fleet-health service, repository database, log parser or custom frontend?

The experiment also tests whether a dedicated read-only GitHub App can enforce private-repository least privilege while the official Grafana GitHub data source supplies workflow, Renovate pull-request and configuration-warning state.

## Validated runtime

```text
Grafana Cloud, EU Germany
Grafana 13.2.0-29856245512
Grafana GitHub data source 2.8.0
OpenTelemetry Collector contrib 0.156.0, pinned by image digest
GitHub-hosted ephemeral runner
configuration provisioned and removed as code
```

The final workflow commit was `6b7612b9dadbf14ca7281ced010bc7c6ed7e55ed`. Run `30592281594` completed successfully in 227 seconds.

## Result

The complete path worked:

```text
GitHub Actions
→ pinned OpenTelemetry Collector
→ Grafana Cloud Metrics
→ Fleet Health dashboard
→ Grafana Alerting
→ webhook notification
```

All final assertions passed. The experiment created its Grafana folder, GitHub data source, dashboard, contact point and alert rule through HTTP APIs, validated them, and removed them in `finally` cleanup.

## GitHub App boundary

The dedicated App installation contained exactly one repository:

```text
betabitplus-template-lab/lab-control
```

Permissions were read-only:

```text
Actions: read
Contents: read
Issues: read
Metadata: read
Pull requests: read
```

| Check | Result |
|---|---:|
| installation repository count | 1 |
| selected `lab-control` repository | HTTP 200 |
| unselected private repository | HTTP 404 |
| selected workflow-runs endpoint | HTTP 200, 7 runs |

This confirms the private-access boundary. Owner-wide GitHub search still returned public repositories outside the App installation because public GitHub data is not hidden by an installation boundary. Consequently, repository search results must not be interpreted as the managed-fleet inventory.

The dashboard used a standard exact-value Grafana transformation for the lab fleet row:

```text
filterByValue: name equals lab-control
```

Production must derive this filter from the committed fleet inventory rather than from App visibility.

## Official GitHub data source

The data source health check returned `OK`.

| Query | Result |
|---|---:|
| Workflows | 19 rows |
| Workflow runs | 7 rows |
| Open Renovate pull requests | 7 rows |
| Configuration-warning issues | 0 rows |
| Releases | 0 rows |
| Unselected private repository | denied |

Zero-row issue and release queries completed without an error and are valid empty dashboard states.

### Workflow-run contract finding

Version `2.8.0` has a frontend/backend field-name mismatch. The frontend type names the workflow selector `workflowID`, while the Go backend deserializes `options.workflow`. Using the backend field returned workflow runs successfully.

This is a provisioning compatibility detail, not a reason to add a custom GitHub exporter.

## Cloud metric contract

Seven metric names were ingested:

```text
ternforge_fleet_expected_repositories
ternforge_fleet_observed_repositories
ternforge_fleet_token_scope_ok
ternforge_update_last_success_unixtime
ternforge_update_processing_duration_seconds
ternforge_update_queue_delay_seconds
ternforge_update_run_success
```

Bounded trigger values were:

```text
manual
nightly
release
```

The final query returned 20 series. No `repository`, `run_id`, `source_sha` or `source_ref` metric labels were present.

Grafana Cloud mapped the custom `ternforge.trigger` resource attribute to `target_info` rather than onto gauge series. A standard OpenTelemetry transform processor copied the bounded resource attribute onto data-point attributes before export. This preserved the validated PromQL contract without adding a custom service or parser.

## Health-state validation

The experiment emitted an unhealthy state:

| Signal | Value |
|---|---:|
| processing duration | 720 seconds |
| run success | 0 |
| expected / observed repositories | 47 / 46 |
| token scope valid | 0 |
| time since last success | about 200,008 seconds |

The Cloud alert became active and a new domain `firing` notification was delivered by HTTP `POST` to the webhook endpoint.

It then emitted a healthy state:

| Signal | Value |
|---|---:|
| processing duration | 180 seconds |
| run success | 1 |
| expected / observed repositories | 47 / 47 |
| token scope valid | 1 |
| time since last success | about 9 seconds |

The domain alert resolved. Grafana service alerts such as `DatasourceNoData` and `DatasourceError` were explicitly excluded from the domain-notification assertion.

Repeated lab executions initially reused the same alert fingerprint and were deduplicated by Alertmanager. The final test used a unique lab-only alert title derived from the workflow run ID. Metric labels and the proposed production alert contract remained unchanged.

## Dashboard

The dashboard contained seven panels:

1. Processing duration
2. Last run success
3. Fleet coverage gap
4. Token scope valid
5. Processing and queue delay
6. Managed repositories
7. Open Renovate pull requests

Grafana rendered it successfully as a 1600 × 1000 PNG of 216,951 bytes. The render is stored in [`grafana-cloud-fleet-health-20260731.png`](grafana-cloud-fleet-health-20260731.png).

## Significant failed attempts

* Run `30589524004`: the Collector container could not read a runtime configuration stored as mode `0600`; the ephemeral read-only mounted file must be readable by the container UID.
* Run `30589643141`: Grafana Cloud plugin installation was asynchronous; provisioning failed until installation completed.
* Run `30589765258`: the trigger resource attribute appeared only in `target_info`; a standard OTel transform processor was required.
* Run `30590602059`: workflow runs worked with `options.workflow`; binary PNG response handling still failed.
* Run `30590911924`: webhook verification raced delayed Cloud delivery and service NoData notifications.
* Run `30591594201`: repeated identical alert fingerprints were deduplicated; the final lab cycle isolated the notification fingerprint without increasing metric cardinality.

These attempts produced concrete compatibility and provisioning requirements rather than new architectural components.

## Limits

The experiment validates organization-owned lab repositories. It does not change the project constraint against using a GitHub Organization for the production fleet.

The exact candidate condition “more than ten minutes for two consecutive runs” still requires bounded cross-run state and was not introduced. The validated alert is one completed release-triggered run greater than 600 seconds.

The experiment does not establish production thresholds. Thresholds remain candidates until representative production-shaped history exists.

## Conclusion

The minimal managed architecture is viable:

```text
bounded Renovate/OpenTelemetry metrics
→ Grafana Cloud Metrics

GitHub current state
→ official Grafana GitHub data source
→ dedicated read-only GitHub App

visualization and action
→ one Fleet Health dashboard
→ Grafana Alerting
```

A custom exporter, fleet-health service, database, log parser, Loki deployment and Backstage instance are not required for the initial observability path.

Machine-readable evidence is in [`grafana-cloud-fleet-health-20260731.json`](grafana-cloud-fleet-health-20260731.json).
