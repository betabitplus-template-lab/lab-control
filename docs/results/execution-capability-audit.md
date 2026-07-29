# Final experiment execution capability audit

Date: 2026-07-14
Branch: `experiment/final-platform-20260714`
Scope: `betabitplus-template-lab/*` writes only
Production baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`
Informational current `dev` HEAD: `d59582375855cff69fb165e467dc5847bc75ca99`

## Safety boundary

The connected GitHub identity can see both the `betabitplus` user installation and the `betabitplus-template-lab` organization installation. Therefore every mutation from this experiment must use an exact repository name beginning with `betabitplus-template-lab/`. No mutation API is permitted for `betabitplus/*`.

The lab installation currently exposes eight private repositories and reports admin/push access to them. Existing tags, component commits, PR evidence, ADR 0001 and first-stage results are treated as immutable evidence.

## Available here

- Read public production source and metadata through the GitHub connector at an exact commit.
- Read private lab repositories, PRs, commits, workflow runs, jobs, logs and artifacts through the GitHub connector.
- Create lab branches, commits/files and pull requests in already-installed lab repositories.
- Inspect and document implementation, prepare Renovate presets, reusable workflow sources, OpenTofu configuration, policy prototypes, tests and result documents.
- Observe GitHub Actions runs caused by committed lab changes when the required repository/secret/settings already exist.

## Environment limitations

The execution sandbox has Python 3, `uv`, Node.js, npm, git and jq, but no outbound DNS/network for command-line tools and no local GitHub credential. The following executables are absent: `gh`, `copier`, `renovate`, `tofu`, `terraform`, `actionlint`, `zizmor`, `yq`.

The GitHub connector does not expose operations for:

- organization/repository creation;
- repository topics, default branch, merge settings or Actions variables/secrets;
- repository/organization rulesets and required checks;
- GitHub App installation selection, permissions, private-key rotation or creation of a restricted test credential;
- workflow dispatch;
- release/tag creation, deletion/move attempts or tag-ruleset bypass testing;
- arbitrary Renovate CLI execution and its `dryRun=extract|lookup|full` modes;
- OpenTofu plan/apply and local Copier/private-submodule execution.

The connector also does not provide a complete recursive repository tree/archive API. Exact whole-tree LOC and command-to-module inventory require a local clone or a machine-readable tree export.

## Consequence

All analysis, code/configuration authoring and documentation that do not require those capabilities remain in this branch and are performed by the primary agent. A local agent is needed only for the live GitHub administration, credential-bound negative tests, CLI executions and complete source/evidence export listed in `docs/results/local-agent-handoff.md`.

## Confirmed preserved evidence

- First-stage report: `docs/results/results.md`.
- ADR 0001: `docs/adr/0001-composed-copier-templates.md`.
- Expected-conflict evidence: `sandbox-python-lib#3`, still open and unmerged.
- Production mutation count at the start of this phase: `0`.
