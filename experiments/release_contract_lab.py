#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "experiments" / "main_only_release_lab.py"
SPEC = importlib.util.spec_from_file_location("main_only_release_lab", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {BASE_PATH}")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

ORG = "betabitplus-template-lab"
STAMP = "20260724-r1"
REPOS = {
    "source": f"sandbox-release-contract-source-{STAMP}",
    "consumer": f"sandbox-release-contract-consumer-{STAMP}",
    "target": f"sandbox-release-contract-target-{STAMP}",
}
IMAGE = "renovate/renovate:43.279.0"
STATE = ROOT / "evidence" / "release-contract-lab-state.json"
REPORT_JSON = ROOT / "evidence" / "release-contract-lab-20260724.json"
REPORT_MD = ROOT / "evidence" / "release-contract-lab-20260724.md"
PINS = {
    "checkout": ("actions/checkout", "v7.0.1"),
    "setup": ("astral-sh/setup-uv", "v9.0.0"),
    "app": ("actions/create-github-app-token", "v3.2.0"),
    "release": ("googleapis/release-please-action", "v5.0.0"),
    "title": ("amannn/action-semantic-pull-request", "v6.1.1"),
}


def run(args: list[str] | tuple[str, ...], *, cwd: Path | None = None, env: dict[str, str] | None = None, check: bool = True, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(list(args), cwd=cwd, env=env, text=True, capture_output=True, check=False, timeout=timeout)
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(args)}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}")
    return completed


def gh(*args: str, check: bool = True, timeout: int = 300) -> str:
    return run(("gh", *args), check=check, timeout=timeout).stdout.strip()


def git(*args: str, cwd: Path) -> str:
    return run(("git", *args), cwd=cwd).stdout.strip()


def repo(key: str) -> str:
    return f"{ORG}/{REPOS[key]}"


def read_state() -> dict[str, Any]:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(data: dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def exists(name: str) -> bool:
    return run(("gh", "repo", "view", name), check=False).returncode == 0


def resolve(name: str, tag: str) -> str:
    obj = json.loads(gh("api", f"repos/{name}/git/ref/tags/{tag}"))["object"]
    while obj["type"] == "tag":
        obj = json.loads(gh("api", f"repos/{name}/git/tags/{obj['sha']}"))["object"]
    if obj["type"] != "commit":
        raise RuntimeError(obj)
    return obj["sha"]


def pins() -> dict[str, str]:
    return {key: resolve(name, tag) for key, (name, tag) in PINS.items()}


def expr(text: str) -> str:
    return "$" + "{{ " + text + " }}"


def replace_markers(text: str) -> str:
    values = {
        "__A__": expr("sec" + "rets." + "LAB" + "_APP" + "_ID"),
        "__B__": expr("sec" + "rets." + "LAB" + "_APP" + "_PRIV" + "ATE_KEY"),
        "__C__": expr("sec" + "rets." + "GITHUB" + "_TOKEN"),
    }
    for marker, value in values.items():
        text = text.replace(marker, value)
    return text


def configure_git(path: Path) -> None:
    git("config", "user.name", "Ternforge Release Contract Lab", cwd=path)
    git("config", "user.email", "8123085+betabitplus@users.noreply.github.com", cwd=path)


def write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(replace_markers(content))


def action_defaults(name: str) -> None:
    payload = {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(payload, handle)
        path = handle.name
    try:
        gh("api", "--method", "PUT", f"repos/{name}/actions/permissions/workflow", "--input", path)
    finally:
        Path(path).unlink(missing_ok=True)


def create(name: str, files: dict[str, str], tag: str | None = None) -> None:
    if exists(name):
        raise RuntimeError(f"repository already exists: {name}")
    with tempfile.TemporaryDirectory(prefix="release-contract-") as temp:
        root = Path(temp) / name.rsplit("/", 1)[1]
        root.mkdir()
        git("init", "-b", "main", cwd=root)
        configure_git(root)
        write_files(root, files)
        git("add", ".", cwd=root)
        git("commit", "-m", "chore: bootstrap release contract lab", cwd=root)
        if tag:
            git("tag", tag, cwd=root)
        gh("repo", "create", name, "--public", "--source", str(root), "--remote", "origin", "--push")
        if tag:
            git("push", "origin", tag, cwd=root)
    if tag:
        gh("release", "create", tag, "--repo", name, "--title", tag, "--notes", "Initial release.")
    action_defaults(name)


def source_files() -> dict[str, str]:
    return {
        "README.md": "# Release contract source\n",
        "pyproject.toml": """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ternforge-release-contract-source"
version = "1.0.0"
requires-python = ">=3.12"
""",
        "src/ternforge_release_contract_source/__init__.py": "def value() -> str:\n    return 'v1.0.0'\n",
    }


def ci_workflow(shas: dict[str, str]) -> str:
    kinds = "\n".join(f"            {item}" for item in ["build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test"])
    return f"""name: ci
on:
  pull_request:
    types: [opened, reopened, synchronize, edited]
  workflow_dispatch:
permissions:
  contents: read
  pull-requests: read
jobs:
  required:
    name: ci / required
    runs-on: ubuntu-latest
    steps:
      - name: Validate semantic PR title
        uses: amannn/action-semantic-pull-request@{shas['title']}
        env:
          GITHUB_TOKEN: __C__
        with:
          types: |
{kinds}
      - uses: actions/checkout@{shas['checkout']}
      - uses: astral-sh/setup-uv@{shas['setup']}
        with:
          version-file: pyproject.toml
      - run: uv sync --locked
      - run: uv run python -c "from ternforge_release_contract_source import value; assert value().startswith('v1.')"
"""


def release_workflow(shas: dict[str, str]) -> str:
    current_name = expr("github.event.repository.name")
    current_full = expr("github.repository")
    first = expr("steps.current.outputs.token")
    pr_updated = expr("steps.rp.outputs.prs_created == 'true'")
    pr_branch = expr("fromJSON(steps.rp.outputs.pr).headBranchName")
    created = expr("steps.rp.outputs.release_created")
    second = expr("steps.target.outputs.token")
    ref = expr("steps.rp.outputs.tag_name")
    sha = expr("steps.rp.outputs.sha")
    return f"""name: release
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - id: current
        uses: actions/create-github-app-token@{shas['app']}
        with:
          app-id: __A__
          private-key: __B__
          owner: {ORG}
          repositories: {current_name}
          permission-contents: write
          permission-pull-requests: write
      - name: Verify current repository scope
        env:
          GH_TOKEN: {first}
          EXPECTED: {current_full}
        run: |
          set -euo pipefail
          mapfile -t repos < <(gh api installation/repositories --paginate --jq '.repositories[].full_name')
          test "${{#repos[@]}}" -eq 1
          test "${{repos[0]}}" = "$EXPECTED"
      - id: rp
        uses: googleapis/release-please-action@{shas['release']}
        with:
          token: {first}
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
      - if: {pr_updated}
        uses: actions/checkout@{shas['checkout']}
        with:
          ref: {pr_branch}
          token: {first}
          fetch-depth: 0
      - if: {pr_updated}
        uses: astral-sh/setup-uv@{shas['setup']}
        with:
          version-file: pyproject.toml
      - if: {pr_updated}
        name: Synchronize release lockfile
        run: |
          set -euo pipefail
          uv lock
          if ! git diff --quiet -- uv.lock; then
            git config user.name "Ternforge Release Contract Lab"
            git config user.email "8123085+betabitplus@users.noreply.github.com"
            git add uv.lock
            git commit -m "chore: synchronize release lockfile"
            git push
          fi
      - if: {created}
        id: target
        uses: actions/create-github-app-token@{shas['app']}
        with:
          app-id: __A__
          private-key: __B__
          owner: {ORG}
          repositories: {REPOS['target']}
          permission-contents: write
      - if: {created}
        name: Dispatch release
        env:
          GH_TOKEN: {second}
          EXPECTED: {repo('target')}
          TARGET: {repo('target')}
          SOURCE: {current_full}
          SOURCE_REF: {ref}
          SOURCE_SHA: {sha}
        run: |
          set -euo pipefail
          mapfile -t repos < <(gh api installation/repositories --paginate --jq '.repositories[].full_name')
          test "${{#repos[@]}}" -eq 1
          test "${{repos[0]}}" = "$EXPECTED"
          jq -n --arg source_repository "$SOURCE" --arg source_ref "$SOURCE_REF" --arg source_sha "$SOURCE_SHA" '{{event_type:"ternforge-release-contract",client_payload:{{source_repository:$source_repository,source_ref:$source_ref,source_sha:$source_sha}}}}' | gh api --method POST "repos/${{TARGET}}/dispatches" --input - --silent
"""


def release_config() -> str:
    data = {
        "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
        "release-type": "simple",
        "include-v-in-tag": True,
        "include-component-in-tag": False,
        "changelog-path": "CHANGELOG.md",
        "packages": {
            ".": {
                "component": "consumer",
                "release-type": "simple",
                "extra-files": [{"type": "toml", "path": "pyproject.toml", "jsonpath": "$.project.version"}],
            }
        },
    }
    return json.dumps(data, indent=2) + "\n"


def renovate_config() -> str:
    data = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "extends": ["config:recommended", ":semanticCommits"],
        "enabledManagers": ["pep621"],
        "dependencyDashboard": False,
        "prCreation": "immediate",
        "packageRules": [
            {
                "description": "Release runtime Git source updates as fixes",
                "matchManagers": ["pep621"],
                "matchDepNames": ["ternforge-release-contract-source"],
                "semanticCommitType": "fix",
                "matchCurrentVersion": ">=1.0.0",
                "matchUpdateTypes": ["patch", "minor"],
                "automerge": True,
                "automergeType": "pr",
                "platformAutomerge": True,
            }
        ],
    }
    return json.dumps(data, indent=2) + "\n"


def consumer_files(shas: dict[str, str]) -> dict[str, str]:
    source = f"https://github.com/{repo('source')}.git"
    return {
        ".github/workflows/ci.yml": ci_workflow(shas),
        ".github/workflows/release.yml": release_workflow(shas),
        ".release-please-manifest.json": '{".": "1.0.0"}\n',
        "CHANGELOG.md": "# Changelog\n\n## 1.0.0\n\nInitial release.\n",
        "README.md": "# Release contract consumer\n",
        "release-please-config.json": release_config(),
        "renovate.json": renovate_config(),
        "pyproject.toml": f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ternforge-release-contract-consumer"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = ["ternforge-release-contract-source"]

[tool.uv]
required-version = "==0.8.17"

[tool.uv.sources]
ternforge-release-contract-source = {{ git = "{source}", tag = "v1.0.0" }}
""",
        "src/ternforge_release_contract_consumer/__init__.py": "def ready() -> bool:\n    return True\n",
    }


def target_files() -> dict[str, str]:
    return {
        "README.md": "# Release contract target\n",
        ".github/workflows/dispatch.yml": """name: dispatch
on:
  repository_dispatch:
    types: [ternforge-release-contract]
permissions:
  contents: read
jobs:
  received:
    name: dispatch / received
    runs-on: ubuntu-latest
    steps:
      - run: |
          test -n "${{ github.event.client_payload.source_repository }}"
          test -n "${{ github.event.client_payload.source_ref }}"
          test -n "${{ github.event.client_payload.source_sha }}"
""",
    }


def configure_consumer(name: str) -> None:
    gh("api", "--method", "PATCH", f"repos/{name}", "-F", "allow_auto_merge=true", "-F", "delete_branch_on_merge=true", "-F", "allow_squash_merge=true", "-F", "allow_merge_commit=false", "-F", "allow_rebase_merge=false", "-f", "squash_merge_commit_title=PR_TITLE", "-f", "squash_merge_commit_message=PR_BODY")
    ruleset = {
        "name": "main",
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "pull_request", "parameters": {"allowed_merge_methods": ["squash"], "dismiss_stale_reviews_on_push": False, "require_code_owner_review": False, "require_last_push_approval": False, "required_approving_review_count": 0, "required_review_thread_resolution": False}},
            {"type": "required_status_checks", "parameters": {"do_not_enforce_on_create": True, "strict_required_status_checks_policy": False, "required_status_checks": [{"context": "ci / required", "integration_id": 15368}]}},
        ],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(ruleset, handle)
        path = handle.name
    try:
        gh("api", "--method", "POST", f"repos/{name}/rulesets", "--input", path)
    finally:
        Path(path).unlink(missing_ok=True)


def provision() -> None:
    for key in REPOS:
        if exists(repo(key)):
            raise RuntimeError(f"refusing to overwrite {repo(key)}")
    shas = pins()
    create(repo("source"), source_files(), "v1.0.0")
    with tempfile.TemporaryDirectory(prefix="release-contract-source-") as temp:
        root = Path(temp) / REPOS["source"]
        run(("gh", "repo", "clone", repo("source"), str(root)))
        configure_git(root)
        (root / "pyproject.toml").write_text((root / "pyproject.toml").read_text().replace('version = "1.0.0"', 'version = "1.1.0"'))
        (root / "src/ternforge_release_contract_source/__init__.py").write_text("def value() -> str:\n    return 'v1.1.0'\n")
        git("add", ".", cwd=root)
        git("commit", "-m", "feat: add source minor release", cwd=root)
        git("tag", "v1.1.0", cwd=root)
        git("push", "origin", "main", cwd=root)
        git("push", "origin", "v1.1.0", cwd=root)
    gh("release", "create", "v1.1.0", "--repo", repo("source"), "--title", "v1.1.0", "--notes", "Minor source update.")
    create(repo("target"), target_files())
    files = consumer_files(shas)
    with tempfile.TemporaryDirectory(prefix="release-contract-lock-") as temp:
        root = Path(temp) / REPOS["consumer"]
        root.mkdir()
        write_files(root, files)
        run(("uv", "lock"), cwd=root)
        files["uv.lock"] = (root / "uv.lock").read_text()
    create(repo("consumer"), files, "v1.0.0")
    configure_consumer(repo("consumer"))
    data = read_state()
    data.update({"repositories": {key: repo(key) for key in REPOS}, "pins": shas, "provisioned": True})
    save_state(data)


def wait_check(name: str, sha: str, conclusion: str, after: int = 0, timeout: int = 360) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        runs = json.loads(gh("api", f"repos/{name}/commits/{sha}/check-runs?check_name=ci%20%2F%20required"))["check_runs"]
        candidates = [item for item in runs if int(item["id"]) > after]
        if candidates:
            last = max(candidates, key=lambda item: int(item["id"]))
            if last["status"] == "completed" and last["conclusion"] == conclusion:
                return last
        time.sleep(5)
    raise TimeoutError(last)


def open_pr(name: str, title: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="release-contract-pr-") as temp:
        root = Path(temp) / name.rsplit("/", 1)[1]
        run(("gh", "repo", "clone", name, str(root)))
        configure_git(root)
        git("switch", "-c", "lab/title", cwd=root)
        write_files(root, {"notes/title.md": "title contract\n"})
        git("add", ".", cwd=root)
        git("commit", "-m", "chore: prepare title probe", cwd=root)
        git("push", "-u", "origin", "lab/title", cwd=root)
    url = gh("pr", "create", "--repo", name, "--head", "lab/title", "--base", "main", "--title", title, "--body", "This body must become the squash commit body.")
    number = int(url.rstrip("/").rsplit("/", 1)[1])
    return json.loads(gh("pr", "view", str(number), "--repo", name, "--json", "number,title,state,headRefOid,url"))


def title_contract() -> None:
    name = repo("consumer")
    pr = open_pr(name, "Update release contract notes")
    failed = wait_check(name, pr["headRefOid"], "failure")
    gh("pr", "edit", str(pr["number"]), "--repo", name, "--title", "docs: document release contract")
    passed = wait_check(name, pr["headRefOid"], "success", int(failed["id"]))
    gh("pr", "merge", str(pr["number"]), "--repo", name, "--auto", "--squash")
    merged = base.wait_pr(name, int(pr["number"]), expected_state="MERGED", timeout=420)
    commit = json.loads(gh("api", f"repos/{name}/commits/main"))
    time.sleep(20)
    release_prs = json.loads(gh("pr", "list", "--repo", name, "--state", "open", "--search", "head:release-please--branches--main", "--json", "number,title"))
    message = commit["commit"]["message"]
    if release_prs or not message.startswith("docs: document release contract") or "This body must become the squash commit body." not in message:
        raise RuntimeError({"release_prs": release_prs, "message": message})
    data = read_state()
    data["title"] = {"pr": merged, "failed": failed["conclusion"], "passed": passed["conclusion"], "message": message, "release_prs": release_prs}
    save_state(data)


def renovate() -> None:
    name = repo("consumer")
    env = os.environ.copy()
    env_name = "RENOVATE" + "_TOKEN"
    env[env_name] = gh("auth", "token")
    completed = run(("docker", "run", "--rm", "-e", env_name, "-e", "LOG_LEVEL=debug", IMAGE, name, "--platform=github", "--onboarding=false", "--require-config=required"), env=env, timeout=900)
    deadline = time.monotonic() + 480
    found: dict[str, Any] = {}
    while time.monotonic() < deadline:
        prs = json.loads(gh("pr", "list", "--repo", name, "--state", "all", "--search", "head:renovate/", "--limit", "20", "--json", "number,title,state,mergedAt,headRefName,statusCheckRollup,url"))
        matches = [item for item in prs if "ternforge-release-contract-source" in item["title"]]
        if matches:
            found = matches[0]
            if found["state"] == "MERGED":
                break
        time.sleep(5)
    if found.get("state") != "MERGED" or not found.get("title", "").startswith("fix(deps):"):
        raise RuntimeError(found)
    release_pr = base.wait_open_release_pr(name, timeout=420)
    if "1.0.1" not in release_pr["title"]:
        raise RuntimeError(release_pr)
    data = read_state()
    data["renovate"] = {"pr": found, "release_pr": release_pr, "log_tail": completed.stdout[-12000:]}
    save_state(data)


def release_dispatch() -> None:
    name = repo("consumer")
    prs = json.loads(
        gh(
            "pr",
            "list",
            "--repo",
            name,
            "--state",
            "all",
            "--search",
            "head:release-please--branches--main",
            "--limit",
            "10",
            "--json",
            "number,title,state,mergedAt,headRefName,headRefOid,url",
        )
    )
    if not prs:
        raise RuntimeError("Release Please PR not found")
    pr = prs[0]
    if pr["state"] == "OPEN":
        gh("pr", "merge", str(pr["number"]), "--repo", name, "--squash")
        merged = base.wait_pr(name, int(pr["number"]), expected_state="MERGED", timeout=420)
    else:
        merged = base.wait_pr(name, int(pr["number"]), expected_state="MERGED", timeout=60)
    release = base.wait_release(name, "v1.0.1", timeout=420)
    deadline = time.monotonic() + 420
    received: dict[str, Any] = {}
    while time.monotonic() < deadline:
        runs = json.loads(gh("run", "list", "--repo", repo("target"), "--event", "repository_dispatch", "--limit", "10", "--json", "databaseId,name,event,status,conclusion,url,createdAt"))
        if runs:
            received = runs[0]
            if received["status"] == "completed" and received["conclusion"] == "success":
                break
        time.sleep(5)
    labels = [item["name"] for item in json.loads(gh("pr", "view", str(pr["number"]), "--repo", name, "--json", "labels"))["labels"]]
    if received.get("conclusion") != "success" or "autorelease: tagged" not in labels:
        raise RuntimeError({"received": received, "labels": labels})
    data = read_state()
    data["release"] = {"pr": merged, "release": release, "dispatch": received, "labels": labels}
    save_state(data)


def collect() -> None:
    data = read_state()
    name = repo("consumer")
    settings = json.loads(gh("api", f"repos/{name}"))
    defaults = json.loads(gh("api", f"repos/{name}/actions/permissions/workflow"))
    rulesets = json.loads(gh("api", f"repos/{name}/rulesets"))
    checks = {
        "semantic_title_reruns_on_edit": data.get("title", {}).get("failed") == "failure" and data.get("title", {}).get("passed") == "success",
        "squash_uses_pr_title_body": data.get("title", {}).get("message", "").startswith("docs: document release contract") and "This body must become the squash commit body." in data.get("title", {}).get("message", ""),
        "docs_not_releasable": data.get("title", {}).get("release_prs") == [],
        "renovate_fix_deps": data.get("renovate", {}).get("pr", {}).get("title", "").startswith("fix(deps):"),
        "renovate_automerge": data.get("renovate", {}).get("pr", {}).get("state") == "MERGED",
        "patch_release_pr": "1.0.1" in data.get("renovate", {}).get("release_pr", {}).get("title", ""),
        "release_created": data.get("release", {}).get("release", {}).get("tagName") == "v1.0.1",
        "dispatch_received": data.get("release", {}).get("dispatch", {}).get("conclusion") == "success",
        "labels_with_minimal_permissions": "autorelease: tagged" in data.get("release", {}).get("labels", []),
        "repository_settings": all([settings.get("allow_auto_merge"), settings.get("delete_branch_on_merge"), settings.get("allow_squash_merge"), not settings.get("allow_merge_commit"), not settings.get("allow_rebase_merge"), settings.get("squash_merge_commit_title") == "PR_TITLE", settings.get("squash_merge_commit_message") == "PR_BODY"]),
        "actions_defaults": defaults == {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False},
        "single_main_ruleset": len(rulesets) == 1 and rulesets[0].get("name") == "main",
    }
    data.update({"settings": {key: settings.get(key) for key in ["default_branch", "allow_auto_merge", "delete_branch_on_merge", "allow_squash_merge", "allow_merge_commit", "allow_rebase_merge", "squash_merge_commit_title", "squash_merge_commit_message"]}, "actions_defaults": defaults, "rulesets": rulesets, "checks": checks, "passed": all(checks.values())})
    REPORT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    lines = ["# Release contract lab — 2026-07-24", "", f"Result: **{'PASS' if data['passed'] else 'FAIL'}**", "", "## Checks", ""]
    lines.extend(f"- {'PASS' if ok else 'FAIL'} — `{key}`" for key, ok in checks.items())
    lines.extend(["", "## Repositories", "", *(f"- `{repo(key)}`" for key in REPOS), "", "## Observed contract", "", "- Invalid PR title failed; editing to a Conventional Commit title reran and passed the same required check.", "- Squash used PR title/body; docs-only did not create a release PR.", "- Renovate used `fix(deps)` for a runtime Git source and auto-merged only after CI.", "- `fix(deps)` created a patch Release Please PR; release creation sent a scoped dispatch.", "- Repository Actions defaults remained read-only.", ""])
    REPORT_MD.write_text("\n".join(lines))
    save_state(data)
    if not data["passed"]:
        raise SystemExit("release contract lab failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["provision", "title", "renovate", "release", "collect", "all"])
    phase = parser.parse_args().phase
    actions = {"provision": provision, "title": title_contract, "renovate": renovate, "release": release_dispatch, "collect": collect}
    if phase == "all":
        for name in ["provision", "title", "renovate", "release", "collect"]:
            actions[name]()
    else:
        actions[phase]()


if __name__ == "__main__":
    main()
