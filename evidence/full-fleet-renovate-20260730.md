# Full-fleet Renovate scaling lab

## Question

Can one GitHub-hosted Renovate process scan the entire managed fleet quickly enough without source-to-target routing, and can its performance be observed without a separate monitoring service?

## Method

The lab used 84 existing `sandbox-*` repositories. Four deterministic nested cohorts of 10, 25, 50 and 84 repositories were processed serially by Renovate 43.262.4 on `ubuntu-latest`.

Each cohort used an exact repository-scoped, read-only GitHub App installation token. Renovate ran with `dryRun=full`, so it performed dependency extraction and simulated branch, Copier and lockfile updates without creating branches, issues or pull requests. Only the `copier`, `github-actions`, `pep621` and `vendir` managers were enabled.

Every cohort ran once with an empty cache and once with the cache left by the first scan. JSON logs, repository timing splits, GitHub rate-limit snapshots and deterministic selections were uploaded as run artifacts.

The first setup run, `30551413710`, was excluded because the disposable cache mount was not writable and no repository scan completed. The corrected valid run was `30551938503` at commit `6de3f86533602e5097cb10d082e787d2f3f71a8a`.

## Result

All eight valid scans completed successfully.

| Repositories | Image pull | Cold scan | Cold total | Warm scan | Cold p50 repo | Cold p95 repo |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 26 s | 58 s | 1:24 | 48 s | 0.27 s | 36.04 s |
| 25 | 26 s | 2:20 | 2:46 | 2:16 | 1.93 s | 35.82 s |
| 50 | 26 s | 3:09 | 3:35 | 2:54 | 1.40 s | 18.79 s |
| 84 | 28 s | 5:36 | 6:04 | 5:11 | 2.13 s | 20.91 s |

At 84 repositories, 55 repositories spent no more than 500 ms in Renovate's `update` phase. Eleven repositories took more than five seconds, eight more than ten seconds, and five more than twenty seconds. The slowest repository took 40.65 seconds.

The 84-repository cold scan spent:

| Phase | Time |
|---|---:|
| Repository initialization | 46.91 s |
| Dependency extraction | 43.30 s |
| Version lookup | 20.93 s |
| Update generation | 194.76 s |
| Process overhead outside repository totals | 5.03 s |

Update generation consumed 59% of repository time. The slowest repository spent 37.44 seconds in `update`; its work included installing Python and Copier, running `copier update`, and regenerating uv lockfiles. Therefore repository count alone is not the main cost. The number and type of active updates determine the long tail.

A linear fit across this deliberately update-heavy sample was approximately:

```text
scan ≈ 30 seconds + 3.57 seconds × repositories
```

Including the observed image pull, that sample crosses five minutes at about 67 repositories. This is not a general capacity limit: `dryRun=full` did not persist simulated updates, so the second pass repeated expensive work that a converged production fleet would usually not repeat.

Using only the observed non-update phases gives a separate no-expensive-update scenario:

```text
total ≈ 28 seconds image pull + 5 seconds process overhead
        + 1.32 seconds × repositories
```

That scenario estimates roughly 2:45 for 100 repositories, 4:58 for 200, 7:10 for 300 and 11:35 for 500. These values are planning estimates, not measured guarantees.

The warm cache reduced the 84-repository scan by 25 seconds. It did not remove Copier or lockfile work, so persistent cache storage is not a first-order scaling solution for this workload.

The 84-repository cold scan consumed 53 of 8,500 GitHub core rate-limit units. GitHub API quota was not close to the limiting boundary.

## Observability

Renovate's existing JSON log already contains the required measurements. A normal run can publish, without an external metrics service:

* fleet size and total duration;
* p50, p95 and maximum repository duration;
* time spent in `init`, `extract`, `lookup` and `update`;
* the slowest repositories;
* remaining GitHub API quota.

A GitHub Step Summary provides the immediate view, while one small JSON artifact preserves evidence for comparison. If proactive notification is required, the smallest additional mechanism is one issue that is created or updated only after a chosen threshold is exceeded; performance observation does not need to make an otherwise successful update run fail.

## Conclusion

A single full-fleet Renovate process is technically viable for the measured 84-repository update-heavy lab and remains observable with native GitHub Actions output. It is no longer a sub-three-minute path at that workload: one cold execution took approximately six minutes including image pull.

The useful operating boundary cannot be expressed as repository count alone. It must account for fleet size and active Copier or lockfile work. The experiment supports collecting total duration, phase splits and slowest repositories from every real run before choosing a production threshold or replacing the current routing decision.

Machine-readable observations are in [`full-fleet-renovate-20260730.json`](full-fleet-renovate-20260730.json). The workflow and parser are [`full-fleet-renovate-lab.yml`](../.github/workflows/full-fleet-renovate-lab.yml) and [`full_fleet_renovate_lab.py`](../experiments/full_fleet_renovate_lab.py).
