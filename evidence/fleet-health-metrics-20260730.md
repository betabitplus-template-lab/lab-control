# Fleet health metrics and alerting lab

## Question

Can Ternforge expose a small low-cardinality operational metric contract and use standard Grafana alerts for unhealthy and recovered fleet states without a custom monitoring service?

## Method

Pinned containers were started on a GitHub-hosted runner:

```text
OTLP/HTTP metrics
→ OpenTelemetry Collector Contrib 0.156.0
→ Prometheus 3.13.1
→ Grafana 13.1.0
```

Grafana data source and alert rules were provisioned as code. The lab emitted an unhealthy state, required every alert to fire, emitted a healthy state and required every alert to resolve.

The validated workflow commit was `b7889b0ceb73370f96821b925060e16736619af2`. Run `30584054787` completed successfully in 1 minute 8 seconds.

## Metric contract

```text
ternforge_update_processing_duration_seconds
ternforge_update_queue_delay_seconds
ternforge_update_run_success
ternforge_update_last_success_unixtime
ternforge_fleet_expected_repositories
ternforge_fleet_observed_repositories
ternforge_fleet_token_scope_ok
```

The only project dimension was:

```text
ternforge_trigger = release | nightly | manual
```

The complete lab contract produced 13 Prometheus series. It contained no repository, run-id, source-ref or source-SHA labels.

## Alert contract

The following five Grafana rules were provisioned:

```text
update-run-failed
update-processing-slow
fleet-coverage-mismatch
fleet-token-scope-mismatch
update-recovery-stale
```

Unhealthy input:

```text
processing duration = 720 seconds
run success = 0
expected repositories = 47
observed repositories = 46
token scope ok = 0
last successful run about 200,000 seconds ago
```

All five alerts fired.

Healthy input:

```text
processing duration = 180 seconds
run success = 1
expected repositories = 47
observed repositories = 47
token scope ok = 1
last successful run about 2 seconds ago
```

All five alerts resolved.

## Implementation findings

* Grafana 13 rejects an alert-group interval of 5 seconds because it is not divisible by the 10-second scheduler interval. The validated group interval is 10 seconds.
* OTLP gauge unit `1` creates a Prometheus `_ratio` suffix. The validated contract omits that unit and keeps units in metric names.
* Initial Grafana `DatasourceNoData` during startup is not a real Ternforge domain alert and must be classified separately.
* Workflow-owned operational metrics are simpler and more stable for critical alerts than converting GitHub table responses through SQL expressions.

## Limitation

The validated latency alert fires when a completed release-triggered run exceeds 600 seconds.

A strict rule such as:

```text
two consecutive completed runs exceed 10 minutes
```

requires cross-run state. A latest-value gauge alone cannot prove consecutive history. Implementing this exactly would require either validated GitHub workflow-run history with `Actions: read` or another persisted state mechanism. It was not silently approximated in this experiment.

## Conclusion

The seven-metric contract is sufficient for the critical Fleet Health rows and alerts while remaining small and low-cardinality. No custom monitoring service, repository labels or log parser is required.

Machine-readable evidence is in [`fleet-health-metrics-20260730.json`](fleet-health-metrics-20260730.json).
