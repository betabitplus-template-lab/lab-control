# Local agent handoff: Ternforge targeted live validation only

This instruction contains only work that the primary environment cannot execute because it lacks outbound CLI network access, a local GitHub credential and GitHub administration endpoints. Do not redo architecture analysis or old lab experiments. Do not write the final Ternforge verdict.

## 0. Immutable safety boundary

Production is strictly read-only:

```text
betabitplus/py-lib-starter
d59582375855cff69fb165e467dc5847bc75ca99
```

Never create or mutate production commits, branches, tags, releases, PRs, workflow runs, settings, secrets, rulesets or App installations.

All mutations must be inside:

```text
betabitplus-template-lab
```

Preserve every existing repository, branch, tag, PR, issue, workflow run, report and evidence. Do not force-push or delete anything. Do not modify or merge `sandbox-python-lib#3`.

Never create repositories whose actual name starts with `ternforge-`. Use only the exact `sandbox-ternforge-*` names below. Repositories must be public. Do not enable automerge. Do not use paid-plan features, self-hosted services or persistent PATs.

Before any write, prove the active credential has no production write/admin access. Stop if that cannot be proved.

## 1. Required local capabilities

Required tools:

```text
git
gh
python >= 3.13
uv
copier
tofu
jq
pre-commit
node/npm
renovate-config-validator
actionlint
zizmor
```

Use Mend Renovate Community Cloud, not a local/self-hosted Renovate execution, for all required updater PR evidence. Local Renovate may be used only for non-mutating extraction diagnostics after a hosted failure, and such use must be labeled diagnostic rather than PASS evidence.

Record exact versions in `handoff-ternforge-live/tools.json`.

## 2. Credential proof

Save redacted outputs under `handoff-ternforge-live/security/`:

```bash
gh auth status
gh api user --jq '{login,id}'
gh api repos/betabitplus-template-lab/lab-control \
  --jq '{full_name,permissions,visibility,default_branch}'
gh api repos/betabitplus/py-lib-starter \
  --jq '{full_name,permissions,visibility,default_branch}'
```

Accept production only when `push=false` and `admin=false`, or the request is denied. Never print tokens, private keys, authorization headers or installation tokens.

Clone production only as a detached read-only source:

```bash
git clone --filter=blob:none --no-checkout \
  https://github.com/betabitplus/py-lib-starter.git work/py-lib-starter
git -C work/py-lib-starter checkout --detach \
  d59582375855cff69fb165e467dc5847bc75ca99
test -z "$(git -C work/py-lib-starter status --porcelain)"
```

Clone the prepared control branch:

```bash
git clone https://github.com/betabitplus-template-lab/lab-control.git work/lab-control
git -C work/lab-control checkout experiment/ternforge-targeted-20260717
```

Do not edit that branch. Return evidence separately; the primary agent will integrate it.

## 3. Create only these public sandbox repositories

```text
sandbox-ternforge-components
sandbox-ternforge-template-infra-repository
sandbox-ternforge-template-py-library
sandbox-ternforge-infra-ci
sandbox-ternforge-infra-updates
sandbox-ternforge-tooling-py-runtime
sandbox-ternforge-tooling-py-policy
sandbox-ternforge-tooling-py-testkit
sandbox-ternforge-consumer-infra
sandbox-ternforge-consumer-py
sandbox-ternforge-repository-control
```

Rules:

- create with no ruleset and no auto-initialized protected branch;
- default automerge off;
- keep all repositories after the experiment;
- archive only after all evidence is collected, never delete;
- do not reuse an existing repository name silently; if any name exists, report it and create a unique suffix `-20260717` without deleting the existing repository.

Save repository creation responses and initial settings JSON.

## 4. Responsibility-first components and template fixtures

### 4.1 Components repository

Create exactly this responsibility taxonomy:

```text
components/
├── agents/
│   ├── base/
│   └── py-library/
├── repository/
│   ├── base/
│   └── copier/
├── project/
│   └── py/
│       ├── base/
│       └── library/
├── quality/
│   └── py/
└── delivery/
    ├── updates/
    ├── ci/py-library/
    └── release/library/
```

Use small real files, not placeholders that cannot render. Include:

- a whole common `.editorconfig` or `.gitattributes` owned by one component;
- one executable acceptance helper with mode `100755`;
- at least two distinct agent files/subdirectories, one from `agents/base` and one from `agents/py-library`;
- valid Jinja/TOML fragments for one final-template-owned `pyproject.toml`;
- a valid `.gitignore` fragment;
- a thin CI caller fragment/config, Renovate config fragment and release config fixture.

Commit and tag:

```text
v0.1.0
v0.2.0
```

The v0.2 tag must point to a released commit. Add one additional untagged commit after v0.2 solely to test that submodule Renovate does not follow arbitrary default-branch state. Do not tag that final commit.

### 4.2 Final templates

Create:

```text
sandbox-ternforge-template-infra-repository
sandbox-ternforge-template-py-library
```

Each must contain exactly one final Copier template, one `copier.yml`, one `.copier-answers.yml` relationship after rendering, and one exact-SHA submodule at:

```text
template/_components
```

Do not add assembler code, manifests, registry, dependency graph or `WIRING.json`.

Use all three composition forms:

1. whole common file through symlink;
2. distinct `.agents/` files/subdirectories from multiple components;
3. final-template-owned compound file with multiple Jinja fragment includes.

Acceptance must fail on:

- any broken symlink;
- `_components` leakage into rendered output;
- any generated reference to an absent `_components` path;
- duplicate output ownership;
- lost executable mode on POSIX;
- invalid TOML/YAML;
- conflict markers.

Record `find -L`, `git ls-files -s`, rendered snapshots and command exit codes. The one-owner mapping may be a generated ephemeral report in evidence, but must not be committed as `WIRING.json` or another manifest.

### 4.3 Template versions and Copier ownership

Create `v0.1.0` and `v0.2.0` tags for both templates.

Infra v0.1 fresh render must contain only:

```text
.agents/
.editorconfig
.gitattributes
.gitignore
LICENSE
.github/pull_request_template.md
.copier-answers.yml
README.md
```

Before v0.1→v0.2 update:

- edit `README.md` as a user;
- add one unrelated user file;
- edit one template-managed file;
- update the corresponding managed file in template v0.2.

Record normal update behavior. Then create a separate clean consumer, delete README before update, and record whether Copier restores it. Do not add `_skip_if_exists`, migration or task before this result. If README remains deleted, accept that as create-once semantics. If it is restored, report it; do not invent a workaround in this handoff.

Py-library fresh render must include:

```text
src/
tests/
docs/
examples/
workbench/
README.md
CHANGELOG.md
pyproject.toml
uv.lock
.pre-commit-config.yaml
.github/workflows/ci.yml
renovate.json5
release-please-config.json
.release-please-manifest.json
```

Treat `src`, `tests`, `docs`, `examples`, `workbench` and `README.md` as user-owned after creation using declarative Copier ownership/exclusion only. Do not use tasks, migrations, extensions or trust.

Before update, make representative edits in every user-owned area. In v0.2 change only managed surfaces:

- CI caller;
- pre-commit config;
- quality configuration;
- Renovate config;
- repository metadata.

Run `copier update` without `--trust`. Verify user areas survive, managed files update, no silent loss occurs, clean cases have no unexplained `.rej`, and a deliberate overlap in one managed file creates visible conflict evidence.

## 5. Mend Renovate Community Cloud live PRs

Install Community Cloud only on the sandbox repositories that require it. Automerge must remain off. Save installation/repository-selection metadata without credentials and save job URLs/log exports.

### 5.1 Components submodule

Initial template gitlinks must point to components `v0.1.0`. Configure built-in `git-submodules` only, opted in explicitly.

Test the smallest documented release configuration. The candidate `.gitmodules` may use `branch = v0.1.0` because Renovate documents tag values there, but all acceptance and rendering must use the committed exact gitlink and must never run `git submodule update --remote` as the version mechanism.

Required evidence:

- hosted Renovate detects v0.2.0;
- PR changes the exact gitlink and any necessary `.gitmodules` version marker only;
- PR does not move to the later untagged default-branch commit;
- template acceptance runs and passes;
- PR is reviewable and unmerged until evidence is captured.

If built-in behavior follows the untagged commit or cannot express released versions, mark FAIL/CONDITIONAL and record exact logs/config. Do not write a custom updater.

### 5.2 Copier update

Render both consumer repositories from v0.1.0 and push their user modifications. Release template v0.2.0, then require hosted Renovate to create real Copier PRs.

Verify:

- `.copier-answers.yml` is detected;
- update runs without unsafe mode/trust;
- no private token wiring exists for these public repos;
- user-owned areas survive;
- managed files change;
- CI runs.

### 5.3 Reusable workflow exact SHA

In `sandbox-ternforge-infra-ci`, create one reusable workflow:

```text
.github/workflows/python-library.yml
```

Its required Ubuntu job runs directly:

```text
uv sync --frozen --all-groups
ruff check
ruff format --check
pyright
pytest
uv build
```

Create release tags `v0.1.0` and `v0.2.0`. The consumer caller must use job-level syntax:

```yaml
uses: betabitplus-template-lab/sandbox-ternforge-infra-ci/.github/workflows/python-library.yml@<40-char-sha> # v0.1.0
```

Require hosted Renovate to update the SHA/comment to v0.2.0, change only the caller workflow, and trigger green CI. No workflow publisher App or custom updater is allowed.

The workflow repository itself must run `actionlint`, targeted `zizmor --pedantic --offline` for privileged workflows, and a real smoke caller. Record commands and exits.

### 5.4 Tagged Renovate preset

In `sandbox-ternforge-infra-updates`, put a valid `default.json` preset and tag v0.1.0/v0.2.0. Consumer config must pin:

```json
{
  "extends": [
    "github>betabitplus-template-lab/sandbox-ternforge-infra-updates#v0.1.0"
  ]
}
```

Require hosted Renovate to update the pinned tag, then run:

```bash
renovate-config-validator --strict
```

Verify no dependency on `main` and no recursive/broken config.

### 5.5 `tool.uv.sources` Git tags

Use `sandbox-ternforge-tooling-py-runtime` as the tagged Git dependency and `sandbox-ternforge-consumer-py` as consumer. Start with built-in PEP 621 only:

```toml
[tool.uv.sources]
some-package = { git = "https://github.com/betabitplus-template-lab/sandbox-ternforge-tooling-py-runtime.git", tag = "v0.1.0" }
```

Required evidence:

- whether the tag is detected and updated to v0.2.0;
- `uv.lock` changes;
- lock source resolves to the exact commit behind v0.2.0;
- `uv sync --frozen` passes in a clean clone.

If and only if built-in PEP 621 fails, add one literal custom regex matching this exact `tag` field and use the standard GitHub/Git-tags datasource. Do not create reusable regex infrastructure. Return both the failed built-in logs and successful/failed minimal fallback evidence.

### 5.6 Pre-commit

Enable Renovate's opt-in `pre-commit` manager only for the actual hooks selected in the Python template. Require a real PR that updates hook revisions and passes:

```bash
pre-commit run --all-files
```

If it fails, record the exact manager limitation and test only a standard alternative such as the upstream `pre-commit autoupdate` command in a reviewable workflow. Do not build an updater service.

## 6. Standalone Python tooling split

Use the existing replacement matrix as authoritative. Do not re-audit all modules.

### Runtime

Create from the frozen baseline's `packages/py-lib-runtime` product code. It must:

- build and test standalone;
- contain only runtime API/product code;
- have no runtime dependency on policy or testkit;
- not require the old monorepo root.

### Policy

Use the already-proven minimal policy behavior from `work/lab-control/experiments/minimal-policy`. It must be a standalone package/dev tool and must not wrap Ruff, Pyright, pytest, import-linter or uv.

### Testkit

Extract and preserve the meaningful old test-support behavior marked `DEFER` in the replacement matrix:

```text
VCR helpers
console helpers
image helpers
e2e helpers
common fixtures/setup/path helpers
```

Move it into its own public package namespace and adapt imports only as needed. Preserve representative tests from the frozen baseline and add standalone tests for each helper family. It may depend on runtime only where an actual helper requires runtime behavior; policy must not be a runtime dependency. No circular dependencies are allowed.

Tag each repository v0.1.0 and v0.2.0. Do not publish to PyPI.

In one consumer prove:

- runtime in `[project.dependencies]`;
- policy in a dev dependency group;
- testkit in a test dependency group;
- all three use `tool.uv.sources` Git tags;
- `uv.lock` records exact commits;
- clean `uv sync --frozen --all-groups` passes;
- representative runtime, policy and testkit use/tests pass.

Return the exact old→new file map and any deleted wrappers. Do not broaden the split beyond replacement-matrix decisions.

## 7. OpenTofu repository-control live test

Use `sandbox-ternforge-repository-control` as the OpenTofu control repository and create one additional public target repository named:

```text
sandbox-ternforge-controlled-repository
```

This one additional name is allowed solely because it is created by the OpenTofu experiment. Preserve it after testing.

Use current pinned versions selected deliberately; record why. The provider observed by the primary audit was 6.13.0, so do not silently reuse 6.6.0.

OpenTofu state must stay uncommitted. Do not deploy a paid/cloud backend. Configure a normal backend block/interface so a standard remote backend can be supplied later without changing resources.

Apply in this exact order:

1. create public repository with no active ruleset;
2. create/push `dev`;
3. create `main`;
4. set intended default branch;
5. create a real CI workflow and obtain the exact required check name from a successful run;
6. add one branch ruleset targeting both `dev` and `main`;
7. add one tag ruleset targeting `v*`.

Branch ruleset:

```text
PR required
required CI
force push blocked
deletion blocked
required approving reviews = 0
```

Do not set last-push approval, stale-review dismissal, `TEMPLATE_LANE`, or separate duplicate rulesets for dev/main.

Tag ruleset:

```text
delete blocked
non-fast-forward update blocked
```

Practical tests, each with command, exit code and GitHub response:

- bootstrap completes before ruleset activation;
- solo owner can merge a normal PR with zero approvals after CI;
- feature→dev works;
- dev→main works;
- direct push to protected branch fails;
- force push fails;
- deletion of protected branch fails;
- v0.1.0 can be created by the chosen allowed owner/release actor;
- v0.1.0 cannot be moved or deleted;
- repeat `tofu plan` shows no drift;
- disabling or rolling back a bad ruleset through OpenTofu restores access.

Explicitly state in evidence:

```text
dev → main is a workflow convention; the ruleset does not restrict PR source branch.
```

Do not build a promotion guard.

## 8. Targeted rollback evidence

Record only:

1. components gitlink back to previous released SHA;
2. close without merge or revert a Copier update PR;
3. reusable workflow caller SHA back to v0.1.0;
4. Git dependency tag back to v0.1.0 plus regenerated `uv.lock` and frozen sync;
5. OpenTofu ruleset disable/rollback.

No fleet-wide edits or custom control plane.

## 9. Evidence bundle

Return a directory or ZIP:

```text
handoff-ternforge-live/
  report.md
  report.json
  tools.json
  security/
    credential-boundary.json
  repositories/
    repositories.json
    <repo>/
      branches.json
      tags.json
      prs.json
      settings.json
  experiments/
    composition/
    copier-infra/
    copier-py-library/
    renovate-submodule/
    renovate-copier/
    renovate-workflow/
    renovate-preset/
    renovate-uv-source/
    renovate-pre-commit/
    tooling-split/
    opentofu-rulesets/
    rollbacks/
```

Every experiment directory must contain:

```text
commands.log          # command + exit code, secrets redacted
evidence.json         # repository, branch, commit, tag, PR, workflow run
relevant.diff
notes.md
```

`report.json` schema:

```json
{
  "production_baseline": "d59582375855cff69fb165e467dc5847bc75ca99",
  "production_mutations": 0,
  "credential_boundary": "PASS|FAIL|BLOCKED",
  "repositories_created": [],
  "mend_renovate": {
    "installation": "PASS|FAIL|BLOCKED",
    "job_urls": []
  },
  "experiments": {
    "composition_without_wiring": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "copier_infra": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "copier_py_library": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "renovate_submodule_release": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "renovate_copier": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "renovate_reusable_workflow": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "renovate_preset": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "renovate_uv_git_tag_builtin": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "renovate_uv_git_tag_regex_fallback": "NOT_NEEDED|PASS|FAIL|BLOCKED",
    "renovate_pre_commit": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "standalone_runtime": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "standalone_policy": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "standalone_testkit": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "consumer_frozen_lock": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "opentofu_bootstrap_rulesets": "PASS|FAIL|CONDITIONAL|BLOCKED",
    "targeted_rollbacks": "PASS|FAIL|CONDITIONAL|BLOCKED"
  },
  "custom_fallbacks": [],
  "blockers": [],
  "evidence_index": []
}
```

For each result, report facts and raw evidence only. Do not declare `READY TO PLAN TERNFORGE`; the primary agent will classify and write the final report after reviewing the bundle.

## 10. Stop conditions

Stop immediately and return `BLOCKED` if:

- production write access cannot be excluded;
- a requested operation requires a paid plan;
- Mend Community Cloud cannot be installed without expanding access outside sandbox repos;
- a credential or secret would need to be committed or printed;
- the only path to PASS requires a forbidden custom service/controller/framework;
- existing evidence would need deletion, force-push, tag movement or PR rewrite.
