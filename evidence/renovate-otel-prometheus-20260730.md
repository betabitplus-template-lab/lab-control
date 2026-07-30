# Renovate OpenTelemetry to Prometheus lab

## Question

Can Ternforge use standard OpenTelemetry and Prometheus components for useful Renovate performance metrics at a near-term fleet size without a custom log parser, excessive cardinality or material scan overhead?

## Method

The same deterministic 25-repository cohort was processed twice by pinned Renovate 43.262.4 in `dryRun=full`: one control scan and one scan exporting OTLP/HTTP traces.

The instrumented path was:

```text
Renovate traces
→ OpenTelemetry Collector Contrib
→ spanmetrics connector
→ Prometheus OTLP receiver
```

All containers were pinned by immutable digest. The GitHub App token was read-only and scoped to exactly the 25 repositories.

The initial configuration converted every Renovate span. After that run exposed high-cardinality span names, a corrected declarative Collector filter retained only:

```text
run
repository
init / onboarding / extract / lookup / update
```

Per-run identifiers were not promoted into persistent metric labels.

## Result

The initial run `30560478456` proved that the standard telemetry path worked but also showed why unfiltered spanmetrics is unsafe as a default:

* all 25 repository spans were received;
* run duration and repository p95 were queryable;
* 1,305 Prometheus series were created;
* span names included repository filesystem paths, branch names, raw package-manager commands and other unbounded values.

The run conclusion was failed only because the evidence parser expected `calls_total` for the root `run` span. The duration count and duration sum were present, and both Renovate scans succeeded. The assertion was corrected without changing the experiment question.

The corrected valid run `30561416059` completed successfully:

| Measurement | Control | Instrumented |
|---|---:|---:|
| Renovate scan | 140 s | 148 s |
| Difference | — | +8 s |

The bounded metric surface contained:

| Observation | Result |
|---|---:|
| Repository spans | 25 |
| Root run duration count | 1 |
| Root run duration | 143.73 s |
| Repository p95 | 41.25 s |
| Renovate phase dimensions | 5 |
| Prometheus series | 105 |

The only span names were `run`, `repository`, `init`, `onboarding`, `extract`, `lookup` and `update`. Cardinality fell from 1,305 to 105 series for the same cohort.

The instrumented scan was 8 seconds slower than its paired control, approximately 5.7%. One pair cannot establish stable overhead because update-heavy Renovate scans and GitHub-hosted runners vary naturally, but telemetry did not approach an operational boundary for dozens of repositories.

## Conclusion

The standard pipeline is technically sufficient. Ternforge does not need a custom JSON-log metrics parser to obtain run duration, repository count, repository latency distribution or Renovate phase timings.

Prometheus alone is not the complete solution: Renovate emits traces, while the OpenTelemetry Collector `spanmetrics` connector performs the standard trace-to-metric conversion. A declarative bounded filter is required; converting all Renovate spans directly creates unnecessary cardinality even at 25 repositories.

The validated minimal metric contract is:

```text
run duration
repository duration histogram
repository count
init / onboarding / extract / lookup / update duration
workflow conclusion from GitHub Actions
```

Detailed branch, command and filesystem spans should remain traces in a trace backend or ordinary run logs, not metric dimensions.

Machine-readable evidence is in [`renovate-otel-prometheus-20260730.json`](renovate-otel-prometheus-20260730.json). The workflow and configurations are [`renovate-otel-prometheus-lab.yml`](../.github/workflows/renovate-otel-prometheus-lab.yml), [`otel-collector-config.yml`](../experiments/renovate-otel-prometheus/otel-collector-config.yml) and [`prometheus.yml`](../experiments/renovate-otel-prometheus/prometheus.yml).
