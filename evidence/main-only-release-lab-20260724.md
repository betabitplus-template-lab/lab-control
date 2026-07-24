# Main-only release lab — 2026-07-24

Result: **PASS**

## Checks

- PASS — `one_permanent_branch`
- PASS — `template_release_pr_reused`
- PASS — `template_release_minor`
- PASS — `template_consumer_manual`
- PASS — `tool_pre1_manual`
- PASS — `tool_stable_minor_automerge`
- PASS — `tool_major_manual`

## Repositories

- `betabitplus-template-lab/sandbox-main-template-20260724-r4`
- `betabitplus-template-lab/sandbox-main-template-consumer-20260724-r4`
- `betabitplus-template-lab/sandbox-main-tool-20260724-r4`
- `betabitplus-template-lab/sandbox-main-tool-consumer-20260724-r4`

## Observed model

- One permanent `main` branch, squash-only PR flow, one required `ci / required` check.
- Release Please kept one release PR and updated it after a second feature merge.
- Merging the release PR created the expected tag and GitHub Release.
- Copier consumer update stayed open for manual review.
- Pre-1.0 and major tool updates stayed open for manual review.
- Stable minor tool update merged automatically only after consumer CI passed.

## Important findings

- The required check must have the explicit job name `ci / required`; a job id alone produces a different context.
- Release Please needs the repository-scoped GitHub App token in this organization; the default workflow token cannot create its PR.
- `astral-sh/setup-uv@v8` does not resolve; use an exact released tag or immutable SHA.
- Renovate's default two-PR-per-hour limit delayed only the compressed lab sequence; the normal configuration was restored.
