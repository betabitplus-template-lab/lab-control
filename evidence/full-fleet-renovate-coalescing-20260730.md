# Full-fleet Renovate event coalescing lab

## Question

Can a state-based full-fleet Renovate workflow safely keep one running execution and only the newest pending execution, replacing redundant intermediate release events without missing the latest released state?

## Method

The lab used one existing controlled Git dependency:

```text
sandbox-release-contract-consumer-20260724-r1
  ternforge-release-contract-source = v1.1.0
```

Three temporary source tags were created in sequence: `v1.2.0`, `v1.3.0` and `v1.4.0`. Each tag triggered the same workflow concurrency group with `cancel-in-progress: false` and GitHub's default single-pending behavior.

The first execution observed `v1.2.0` with real Renovate `dryRun=full`, uploaded its observation, and then held the concurrency slot for 180 seconds. While it was still running, the `v1.3.0` execution was queued. The `v1.4.0` execution was then queued before the first run completed.

Each executing job used a read-only GitHub App installation token scoped only to the controlled source and consumer repositories. Renovate enabled only the `pep621` manager and could not create branches, issues or pull requests.

## Result

| Event | Run | Queue result | Renovate observation |
|---|---:|---|---|
| `v1.2.0` | `30556211884` | Ran and remained active | Current `v1.1.0`; latest `v1.2.0` |
| `v1.3.0` | `30556423844` | Pending, then replaced and cancelled before any job started | None |
| `v1.4.0` | `30556481913` | Remained as the newest pending run, then ran after `v1.2.0` completed | Current `v1.1.0`; latest `v1.4.0` |

The first job completed at `15:24:52Z`. The final job started at `15:25:12Z`. The running job was not cancelled, the intermediate pending job never executed, and the final real Renovate scan selected the newest available source tag.

All temporary tags were deleted after the experiment. The source returned to its original `v1.1.0` and `v1.0.0` tags.

## Conclusion

Coalescing is safe for this contract because every execution reconciles current state:

```text
release event
→ trigger a full scan
→ Renovate reads current tags and current consumer files
→ produce the newest required update
```

Processing `v1.3.0` separately was unnecessary. The later `v1.4.0` full scan subsumed it and converged to the latest released state.

This result only applies while events are wake-up signals and the workflow remains state-based and duplicate-safe. Coalescing would be unsafe if future event payloads introduced mandatory per-event side effects, counters, destructive operations or correctness that depends on processing every version in order.

Machine-readable evidence is in [`full-fleet-renovate-coalescing-20260730.json`](full-fleet-renovate-coalescing-20260730.json). The workflow and parser are [`full-fleet-renovate-coalescing-lab.yml`](../.github/workflows/full-fleet-renovate-coalescing-lab.yml) and [`renovate_coalescing_lab.py`](../experiments/renovate_coalescing_lab.py).
