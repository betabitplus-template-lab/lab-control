# Reusable workflows results

## Result

**Implementation PASS; private cross-repository execution currently NEGATIVE PASS.**

A representative private reusable workflow was committed to `lab-control` at exact SHA `8947060677a2f051351a56df48d6f50f37a37987`. A downstream caller was committed at `39cd279c9f96a32f467dbfa1aa1014714489e757` and opened as [sandbox-python-platform#3](https://github.com/betabitplus-template-lab/sandbox-python-platform/pull/3).

## Caller reduction

The caller is 12 YAML lines and contains only trigger, read permission, exact reusable-workflow ref, one input and `secrets: inherit`. The reusable implementation owns Linux/macOS jobs, stable check names and secret presence validation.

The prepared production caller example is 14 lines. Representative copied Python CI is approximately 45–70 lines per repository, so central reuse removes most workflow-body duplication. Workflow implementation changes require only a ref bump; template-generated product/config changes still use Copier.

## Live evidence

| Evidence | Result |
|---|---|
| downstream validation run `29371632671` | PASS |
| private reusable caller run `29371633018` | FAIL before jobs |
| jobs returned for failed reusable run | empty list |
| caller pinned to 40-character source SHA | PASS |
| automerge | disabled |

The most likely explanation is missing private workflow access/sharing on the source repository. This is an inference from the pre-job failure, not a claimed GitHub diagnostic string. Handoff 02 must enable organization access for the final `automation` repository and repeat the run.

## Designed acceptance after access enablement

- private source and private caller;
- explicit inputs;
- `secrets: inherit` without secret disclosure;
- `permissions: contents: read` in caller and callee;
- Linux required job plus macOS representative job;
- stable required check name;
- intentional failure input proves failure propagation;
- cancellation remains native GitHub job cancellation;
- caller cannot elevate permissions beyond caller grant;
- exact SHA and tagged refs compared; exact SHA selected.

## Updating the reusable ref

Renovate's GitHub Actions manager can detect reusable workflow `uses:` refs. The permission problem remains: modifying `.github/workflows` requires Workflows write for an App token. The recommended model keeps that permission away from Renovate and uses the bounded trusted updater in `automation/.github/workflows/secure-workflow-update.yml`.

The updater validates one selected repository, one workflow path and two exact SHAs, changes exactly one occurrence, verifies that no other file changed, and opens a PR to `dev`. It never merges. This preserves least privilege and reviewability at the cost of 99 lines of narrowly scoped workflow logic.
