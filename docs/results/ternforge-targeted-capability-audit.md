# Ternforge targeted validation: capability audit

Date: 2026-07-17  
Branch: `experiment/ternforge-targeted-20260717`  
Writable scope: `betabitplus-template-lab/*` only  
Read-only production baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`

## Safety result

The exact production commit exists and was inspected read-only. No production branch, tag, release, PR, workflow, setting, App installation or repository content was mutated.

The connected GitHub App has an installation on `betabitplus-template-lab` with admin/push access to the currently installed public lab repositories. All writes in this phase are restricted to the new branch above in `betabitplus-template-lab/lab-control`.

Existing lab repositories, branches, tags, PRs, reports and evidence are preserved. The new branch starts from `experiment/final-platform-20260714`; it does not rewrite or replace that branch.

## What the primary environment can do

- Read the frozen production repository and exact commit through the GitHub connector.
- Read all installed lab repositories, commits, PRs, workflow runs, logs and artifacts.
- Create new branches, text-file commits and PRs in already installed lab repositories.
- Inspect and classify existing evidence.
- Research current official documentation.
- Author experiment specifications, configurations, reports and evidence schemas.
- Observe workflow runs that are triggered automatically after a commit or PR when the repository and required settings already exist.
- Run local, network-independent Python and shell validation.

## Hard environment limitations

The execution sandbox has no outbound DNS for command-line tools and no local GitHub credential. `git clone`, package/tool installation and networked CLI execution therefore fail. `gh`, `copier`, `tofu`, `renovate`, `pre-commit`, `ruff`, `pyright`, `actionlint` and `zizmor` are not available locally.

The GitHub connector does not expose these required operations:

- create or archive repositories;
- create, move or delete Git tags and GitHub Releases;
- change repository visibility, default branch, merge settings, topics, Actions settings, variables or secrets;
- install/configure Mend Renovate Community Cloud or change GitHub App repository selection/permissions;
- dispatch workflows;
- create/manage/test repository rulesets and required checks;
- run OpenTofu plan/apply;
- execute Copier, Renovate, uv network resolution, pre-commit or GitHub negative push/tag tests from a real clone.

These are the only classes of work handed to the local agent. Architecture analysis, classification and experiment acceptance criteria remain owned by the primary agent.

## Existing lab evidence retained as source of truth

The previous lab already proves the following mechanisms and they must not be repeated merely for reassurance:

- exact-SHA components submodule inside a final Copier template;
- whole-file symlink rendering and Jinja include wrappers;
- `_components` loader visibility with downstream exclusion;
- executable-mode limitation of file symlinks and preservation by executable wrappers;
- ordinary Copier creation/update, unrelated-file preservation and visible conflict markers;
- gitlink-only Renovate PR behavior in the previous private/self-hosted configuration;
- one-line components gitlink rollback;
- reusable-workflow calls and exact-SHA references in the previous configuration;
- direct quality/tooling replacement analysis;
- complete replacement matrix for 25 commands and 127 production modules.

Authoritative inherited documents are:

- `docs/results/results.md`;
- `docs/adr/0001-composed-copier-templates.md`;
- `docs/adr/0002-production-target-architecture.md`;
- `docs/adr/0003-minimal-policy-tooling.md`;
- `docs/results/replacement-matrix.md` and `.json`;
- `docs/results/minimal-custom-surface.md`;
- `docs/results/tool-evaluation.md`;
- `docs/results/final-experiment-results.md` and `.json`.

The new plan supersedes old decisions that depended on a self-hosted Renovate controller, workflow-publisher App, fleet/topic registry, promotion helper, private-plan workaround, committed `WIRING.json`, or combined automation repository.

## Documentation-confirmed points

Current official documentation establishes these expectations but does not replace required live evidence:

- Renovate `git-submodules` is beta and disabled by default. It uses `git-refs`; a `.gitmodules` `branch` value can be a tag, but this breaks normal `git submodule update --remote` semantics. The lab must therefore prove a reviewable release-tag update without relying on `--remote`.
- Renovate Copier detects `.copier-answers*.yml`, uses Git tags and invokes Copier; unsafe features require trust/script enablement. Declarative templates should update without that capability.
- Renovate GitHub Actions supports `uses:` dependencies and digest pinning with a version comment. GitHub itself calls reusable workflows at job level and recommends exact commit SHAs.
- Renovate pre-commit is beta/opt-in and uses GitHub/GitLab tags.
- Renovate PEP 621 recognizes `tool.uv.sources` and `uv.lock`, but its documented datasource is PyPI. Whether a Git-tag source field is upgraded correctly remains an experiment.
- Repository-hosted Renovate presets can be pinned to a Git tag using `#<tag>`.
- uv supports `tool.uv.sources.<name>.git` plus `tag`, and lock/sync workflows.
- GitHub repository rulesets are available for public repositories on the current free plan and can target branches/tags, require PRs/status checks, block force pushes and deletions. Rulesets target destination refs; they do not encode the convention that a PR to `main` must originate from `dev`.
- The current GitHub provider release observed during this audit is `6.13.0`; old lab pin `6.6.0` must not be reused without an explicit compatibility decision.
- Copier documents that a template-originated path deleted by the user is excluded from subsequent updates, while `_skip_if_exists` would ensure/recreate it. The README deletion case is still run once to create direct evidence for the chosen template.

## Consequence

The primary agent can complete document analysis, question classification, fixture/acceptance design and final report integration. A local agent is required only for the live repository/App/tag/workflow/OpenTofu/CLI operations listed in `docs/results/ternforge-local-agent-handoff.md`.
