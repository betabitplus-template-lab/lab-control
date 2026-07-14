# Local agent handoff 01: capabilities and evidence export only

This handoff contains only work blocked by the primary agent's environment. Do not implement architecture, write final conclusions, refactor code, or modify production repositories.

## Objective

Return a machine-readable capability/evidence bundle that lets the primary agent finish the analysis and author the lab changes. The only permitted mutation in this handoff is rotation of the **lab Renovate App private key**, and only when it is confirmed not already rotated after the leaked diagnostic commit.

## Absolute safety rules

1. Use a dedicated lab credential. Before any authenticated command, prove that it cannot write to `betabitplus/py-lib-starter` or any other existing `betabitplus/*` repository.
2. Production is read-only. Do not push, create branches/PRs/issues/tags, dispatch workflows, change settings/topics/secrets, run Renovate, or alter App access in `betabitplus/*`.
3. Do not change existing lab tags `v0.1.0`, `v0.2.0`, `v0.3.0`, component commits C1/C2/C3, `sandbox-python-lib#3`, first-stage evidence, `results.md`, or ADR 0001.
4. Never print token values, private keys, secret values, authorization headers, signed JWTs or installation tokens. Record only credential type, owner, repository allowlist and permission names.
5. Stop immediately if the active credential has write access outside `betabitplus-template-lab/*`.

## Required tools

Use locally installed `git`, `gh`, Python 3.13+, `uv`, `jq`, and a line counter (`tokei`, `scc`, or `cloc`). Install tools locally when missing. Do not commit tool binaries.

## Step 1 — credential boundary proof

Run and redact outputs as needed:

```bash
gh auth status
gh api user --jq '{login,id}'
gh api user/installations --paginate \
  --jq '.installations[] | {id, account: .account.login, repository_selection, permissions}'
```

For the exact active credential, test repository permissions without writing:

```bash
gh api repos/betabitplus-template-lab/lab-control \
  --jq '{full_name,permissions,visibility,default_branch}'
gh api repos/betabitplus/py-lib-starter \
  --jq '{full_name,permissions,visibility,default_branch}'
```

The acceptable production result is `push=false` and `admin=false`, or a 403/404. If production write/admin is true, stop and switch credentials.

Record the exact lab repositories available to the credential:

```bash
gh api installation/repositories --paginate \
  --jq '.repositories[].full_name' | sort
```

## Step 2 — read-only source export

Clone the frozen production baseline without changing it:

```bash
git clone --filter=blob:none --no-checkout \
  https://github.com/betabitplus/py-lib-starter.git work/py-lib-starter
git -C work/py-lib-starter checkout --detach \
  d59582375855cff69fb165e467dc5847bc75ca99
```

Also record current informational `dev` HEAD:

```bash
git -C work/py-lib-starter ls-remote origin refs/heads/dev
```

Create these files under an untracked `handoff-01/` directory; do not commit them to production:

```bash
mkdir -p handoff-01/source

git -C work/py-lib-starter ls-tree -r --long --full-tree HEAD \
  > handoff-01/source/production-tree.txt

git -C work/py-lib-starter ls-files -z \
  'src/py_lib_starter/**' \
  'packages/py-lib-tooling/**' \
  'packages/py-lib-runtime/**' \
  'scripts/**' \
  '.github/workflows/**' \
  '.github/actions/**' \
  'template-components/**' \
  'template-manifests/**' \
  'template-builds/**' \
  'copier.yml' 'renovate.json5' 'pyproject.toml' \
  | tr '\0' '\n' > handoff-01/source/scoped-files.txt
```

Export exact source files needed for analysis as a tarball:

```bash
git -C work/py-lib-starter archive \
  --format=tar.gz \
  --output="$PWD/handoff-01/source/py-lib-starter-d595823-scoped.tar.gz" \
  d59582375855cff69fb165e467dc5847bc75ca99 \
  src packages scripts .github template-components template-manifests \
  template-builds copier.yml renovate.json5 pyproject.toml
```

Generate LOC twice: production logic excluding tests/generated files, and tests separately. Prefer `tokei --output json`; otherwise use `scc --format json` or `cloc --json`. Include the command used and raw JSON output. At minimum split:

- `src/py_lib_starter`;
- `packages/py-lib-tooling/src`;
- `packages/py-lib-runtime/src`;
- tests for each package;
- `scripts`;
- `.github/actions` and workflow YAML;
- `template-components` production sources;
- generated `template-builds` separately.

## Step 3 — lab metadata export

For every existing `betabitplus-template-lab/*` repository, export read-only metadata:

- repository visibility/default branch/merge settings/delete-branch-on-merge;
- topics;
- branches and tags;
- open PRs and issues;
- rulesets;
- Actions permissions and allowed-actions policy;
- Actions variables and secret **names only**;
- installed GitHub Apps and repository selection when visible;
- latest relevant workflow runs and artifact names.

Use `gh api`; save one JSON file per endpoint under `handoff-01/lab-metadata/`. A 403 or unavailable endpoint must be recorded, not worked around with broader credentials.

## Step 4 — token-leakage check and Renovate key status

Identify the timestamp/commit of the old diagnostic leak from lab history and determine whether the Renovate App private key was rotated afterward. Do not expose either old or current key material.

Scan current lab workflow logs and downloaded artifacts for credential-like material. Use patterns for GitHub tokens, PEM headers, `Authorization:`, JWTs and URLs containing credentials. Save only:

- run/artifact identifier;
- file/log location;
- pattern category;
- redacted finding;
- pass/fail.

If the lab Renovate App key has **not** been rotated since the diagnostic leak and the active operator is authorized to manage the App, rotate it now, delete the obsolete key, and record only the rotation timestamp and key identifier/fingerprint if GitHub exposes one. If authorization is missing, record `ROTATION_REQUIRED` and do nothing else.

## Step 5 — local execution capability matrix

Return versions and a smoke result for:

```text
git
gh
python
uv
copier
renovate
node/npm
opentofu (tofu)
actionlint
zizmor
jq
line counter
```

For each tool record `available`, `version`, and whether it can access private lab repositories with the lab credential. Do not run Renovate live and do not run OpenTofu apply in this handoff.

## Required return bundle

Return a ZIP or directory containing:

```text
handoff-01/
  report.md
  report.json
  source/
    production-tree.txt
    scoped-files.txt
    py-lib-starter-d595823-scoped.tar.gz
    loc-production.json
    loc-tests.json
    loc-command.txt
  lab-metadata/
    ... JSON exports ...
  security/
    token-scan.json
    renovate-key-status.json
  tools/
    versions.json
```

`report.json` must include:

```json
{
  "production_baseline": "d59582375855cff69fb165e467dc5847bc75ca99",
  "current_dev_head": "...",
  "production_write_access": false,
  "lab_repositories": [],
  "missing_permissions": [],
  "renovate_key_status": "ROTATED|ALREADY_ROTATED|ROTATION_REQUIRED|UNKNOWN",
  "token_scan": "PASS|FAIL|INCOMPLETE",
  "tools": {},
  "blocked_endpoints": [],
  "notes": []
}
```

Do not create `automation`, `sandbox-process` or `sandbox-provisioned` yet. Do not edit the experiment branch. The primary agent will use this evidence to author the exact configurations before a second, narrower live-execution handoff.
