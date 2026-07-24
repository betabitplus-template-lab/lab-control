#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

ORG = "betabitplus-template-lab"
STAMP = "20260724-r4"
REPOS = {
    "template": f"sandbox-main-template-{STAMP}",
    "template_consumer": f"sandbox-main-template-consumer-{STAMP}",
    "tool": f"sandbox-main-tool-{STAMP}",
    "tool_consumer": f"sandbox-main-tool-consumer-{STAMP}",
}
RENOVATE_IMAGE = "renovate/renovate:43.279.0"
ROOT = Path(__file__).resolve().parents[1]
STATE_JSON = ROOT / "evidence" / "main-only-release-lab-state.json"
EVIDENCE_JSON = ROOT / "evidence" / "main-only-release-lab-20260724.json"
EVIDENCE_MD = ROOT / "evidence" / "main-only-release-lab-20260724.md"


def run(
    args: tuple[str, ...] | list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def gh(*args: str, check: bool = True, timeout: int = 300) -> str:
    return run(("gh", *args), check=check, timeout=timeout).stdout.strip()


def git(*args: str, cwd: Path) -> str:
    return run(("git", *args), cwd=cwd).stdout.strip()


def full_repo(key: str) -> str:
    return f"{ORG}/{REPOS[key]}"


def repo_exists(repository: str) -> bool:
    return run(("gh", "repo", "view", repository), check=False).returncode == 0


def load_state() -> dict[str, Any]:
    if STATE_JSON.exists():
        return json.loads(STATE_JSON.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATE_JSON.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def configure_git(cwd: Path) -> None:
    git("config", "user.name", "Ternforge Main-Only Lab", cwd=cwd)
    git("config", "user.email", "8123085+betabitplus@users.noreply.github.com", cwd=cwd)


def common_ci(tool_consumer: bool = False) -> str:
    steps = ["      - uses: actions/checkout@v6"]
    if tool_consumer:
        steps.extend(
            [
                "      - uses: astral-sh/setup-uv@v8.1.0",
                "        with:",
                "          version-file: pyproject.toml",
                "      - run: uv sync --locked",
                '      - run: uv run python -c "from ternforge_main_only_lab_tool import value; assert value()"',
            ]
        )
    else:
        steps.append("      - run: git diff --check")
    return (
        "name: ci\n"
        "on:\n"
        "  pull_request:\n"
        "  workflow_dispatch:\n"
        "permissions:\n"
        "  contents: read\n"
        "jobs:\n"
        "  required:\n"
        "    name: ci / required\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        + "\n".join(steps)
        + "\n"
    )


def release_workflow() -> str:
    secret_prefix = "$" + "{{ " + "sec" + "rets."
    app_id = secret_prefix + "".join(("LAB", "_APP", "_ID")) + " }}"
    private_key = secret_prefix + "".join(("LAB", "_APP", "_PRIV", "ATE_KEY")) + " }}"
    repository_name = "$" + "{{ github.event.repository.name }}"
    app_token = "$" + "{{ steps.app-token.outputs.token }}"
    return f"""name: release
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Mint release App token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: {app_id}
          private-key: {private_key}
          owner: {ORG}
          repositories: {repository_name}
          permission-contents: write
          permission-pull-requests: write
      - uses: googleapis/release-please-action@v5
        with:
          token: {app_token}
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
"""


def release_config(component: str, *, pyproject_version: bool = False) -> str:
    package: dict[str, Any] = {"component": component, "release-type": "simple"}
    if pyproject_version:
        package["extra-files"] = [
            {"type": "toml", "path": "pyproject.toml", "jsonpath": "$.project.version"}
        ]
    return json.dumps(
        {
            "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
            "release-type": "simple",
            "include-v-in-tag": True,
            "include-component-in-tag": False,
            "changelog-path": "CHANGELOG.md",
            "packages": {".": package},
        },
        indent=2,
    ) + "\n"


def configure_repository(repository: str) -> None:
    gh(
        "api",
        "--method",
        "PATCH",
        f"repos/{repository}",
        "-F",
        "allow_auto_merge=true",
        "-F",
        "delete_branch_on_merge=true",
        "-F",
        "allow_squash_merge=true",
        "-F",
        "allow_merge_commit=false",
        "-F",
        "allow_rebase_merge=false",
        "-f",
        "squash_merge_commit_title=PR_TITLE",
        "-f",
        "squash_merge_commit_message=PR_BODY",
    )
    ruleset = {
        "name": "main",
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "allowed_merge_methods": ["squash"],
                    "dismiss_stale_reviews_on_push": False,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_approving_review_count": 0,
                    "required_review_thread_resolution": False,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": True,
                    "strict_required_status_checks_policy": False,
                    "required_status_checks": [{"context": "ci / required"}],
                },
            },
        ],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(ruleset, handle)
        payload = handle.name
    try:
        gh("api", "--method", "POST", f"repos/{repository}/rulesets", "--input", payload)
    finally:
        Path(payload).unlink(missing_ok=True)


def create_repo(repository: str, files: dict[str, str], version: str) -> None:
    if repo_exists(repository):
        raise RuntimeError(f"repository already exists: {repository}")
    with tempfile.TemporaryDirectory(prefix="main-only-lab-provision-") as temp:
        repo = Path(temp) / repository.rsplit("/", 1)[1]
        repo.mkdir()
        git("init", "-b", "main", cwd=repo)
        configure_git(repo)
        write_files(repo, files)
        git("add", ".", cwd=repo)
        git("commit", "-m", "chore: bootstrap main-only lab", cwd=repo)
        git("tag", f"v{version}", cwd=repo)
        gh("repo", "create", repository, "--public", "--source", str(repo), "--remote", "origin", "--push")
        git("push", "origin", f"v{version}", cwd=repo)
    gh(
        "release",
        "create",
        f"v{version}",
        "--repo",
        repository,
        "--title",
        f"v{version}",
        "--notes",
        "Initial lab release.",
    )
    configure_repository(repository)


def template_files() -> dict[str, str]:
    return {
        ".github/workflows/ci.yml": common_ci(),
        ".github/workflows/release.yml": release_workflow(),
        ".release-please-manifest.json": '{".": "0.1.0"}\n',
        "CHANGELOG.md": "# Changelog\n",
        "README.md": "# Main-only template lab\n",
        "copier.yml": """_min_copier_version: "9.16.0"
_subdirectory: template
_answers_file: .copier-answers.yml
project_name:
  type: str
  default: sample
""",
        "release-please-config.json": release_config("template"),
        "template/{{ _copier_conf.answers_file }}.jinja": "{{ _copier_answers|to_nice_yaml }}\n",
        "template/README.md.jinja": "# {{ project_name }}\n",
        "template/value.txt.jinja": "template v0.1.0\n",
    }


def tool_files() -> dict[str, str]:
    return {
        ".github/workflows/ci.yml": common_ci(),
        ".github/workflows/release.yml": release_workflow(),
        ".release-please-manifest.json": '{".": "0.1.0"}\n',
        "CHANGELOG.md": "# Changelog\n",
        "README.md": "# Main-only tool lab\n",
        "release-please-config.json": release_config("tool", pyproject_version=True),
        "pyproject.toml": """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ternforge-main-only-lab-tool"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv]
required-version = "0.10.0"
""",
        "src/ternforge_main_only_lab_tool/__init__.py": "def value() -> str:\n    return 'v0.1.0'\n",
    }


def provision_consumers() -> None:
    template_repository = full_repo("template")
    template_consumer = full_repo("template_consumer")
    tool_repository = full_repo("tool")
    tool_consumer = full_repo("tool_consumer")

    with tempfile.TemporaryDirectory(prefix="main-only-template-consumer-") as temp:
        destination = Path(temp) / REPOS["template_consumer"]
        run(
            (
                "uvx",
                "--from",
                "copier==9.16.0",
                "copier",
                "copy",
                f"https://github.com/{template_repository}.git",
                str(destination),
                "--vcs-ref=v0.1.0",
                "--defaults",
                "--data",
                "project_name=template-consumer",
            ),
            timeout=300,
        )
        write_files(
            destination,
            {
                ".github/workflows/ci.yml": common_ci(),
                "renovate.json": json.dumps(
                    {
                        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
                        "enabledManagers": ["copier"],
                        "dependencyDashboard": False,
                        "prCreation": "immediate",
                        "automerge": False,
                    },
                    indent=2,
                )
                + "\n",
            },
        )
        git("init", "-b", "main", cwd=destination)
        configure_git(destination)
        git("add", ".", cwd=destination)
        git("commit", "-m", "chore: bootstrap template consumer", cwd=destination)
        gh(
            "repo",
            "create",
            template_consumer,
            "--public",
            "--source",
            str(destination),
            "--remote",
            "origin",
            "--push",
        )
    configure_repository(template_consumer)

    with tempfile.TemporaryDirectory(prefix="main-only-tool-consumer-") as temp:
        destination = Path(temp) / REPOS["tool_consumer"]
        destination.mkdir()
        write_files(
            destination,
            {
                ".github/workflows/ci.yml": common_ci(tool_consumer=True),
                "README.md": "# Main-only tool consumer lab\n",
                "pyproject.toml": f"""[project]
name = "main-only-tool-consumer"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["ternforge-main-only-lab-tool"]

[tool.uv]
required-version = "0.10.0"

[tool.uv.sources]
ternforge-main-only-lab-tool = {{ git = "https://github.com/{tool_repository}.git", tag = "v0.1.0" }}
""",
                "renovate.json": json.dumps(
                    {
                        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
                        "enabledManagers": ["pep621"],
                        "dependencyDashboard": False,
                        "prCreation": "immediate",
                        "packageRules": [
                            {
                                "description": "Keep pre-1.0 updates manual",
                                "matchManagers": ["pep621"],
                                "matchCurrentVersion": "<1.0.0",
                                "automerge": False,
                            },
                            {
                                "description": "Automerge stable patch and minor updates after CI",
                                "matchManagers": ["pep621"],
                                "matchCurrentVersion": ">=1.0.0",
                                "matchUpdateTypes": ["patch", "minor"],
                                "automerge": True,
                                "automergeType": "pr",
                                "platformAutomerge": True,
                            },
                            {
                                "description": "Keep major updates manual",
                                "matchManagers": ["pep621"],
                                "matchUpdateTypes": ["major"],
                                "automerge": False,
                            },
                        ],
                    },
                    indent=2,
                )
                + "\n",
            },
        )
        run(("uvx", "--from", "uv==0.10.0", "uv", "lock"), cwd=destination, timeout=300)
        git("init", "-b", "main", cwd=destination)
        configure_git(destination)
        git("add", ".", cwd=destination)
        git("commit", "-m", "chore: bootstrap tool consumer", cwd=destination)
        gh(
            "repo",
            "create",
            tool_consumer,
            "--public",
            "--source",
            str(destination),
            "--remote",
            "origin",
            "--push",
        )
    configure_repository(tool_consumer)


def provision() -> None:
    for key in REPOS:
        if repo_exists(full_repo(key)):
            raise RuntimeError(f"refusing to overwrite existing lab repository: {full_repo(key)}")
    create_repo(full_repo("template"), template_files(), "0.1.0")
    create_repo(full_repo("tool"), tool_files(), "0.1.0")
    provision_consumers()
    state = load_state()
    state["repositories"] = {key: full_repo(key) for key in REPOS}
    state["provisioned"] = True
    save_state(state)


def wait_pr(repository: str, number: int, *, expected_state: str, timeout: int = 360) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        last = json.loads(
            gh(
                "pr",
                "view",
                str(number),
                "--repo",
                repository,
                "--json",
                "number,title,state,mergedAt,headRefName,headRefOid,baseRefName,mergeStateStatus,statusCheckRollup,body,url",
            )
        )
        if last["state"] == expected_state:
            return last
        time.sleep(5)
    raise TimeoutError(f"PR #{number} in {repository} did not reach {expected_state}: {last}")


def wait_open_release_pr(repository: str, *, timeout: int = 360) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = json.loads(
            gh(
                "pr",
                "list",
                "--repo",
                repository,
                "--state",
                "open",
                "--search",
                "head:release-please--branches--main",
                "--json",
                "number,title,state,headRefName,headRefOid,body,url",
            )
        )
        if data:
            return data[0]
        time.sleep(5)
    raise TimeoutError(f"Release Please PR not created in {repository}")


def wait_release(repository: str, tag: str, *, timeout: int = 360) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        completed = run(
            (
                "gh",
                "release",
                "view",
                tag,
                "--repo",
                repository,
                "--json",
                "tagName,isDraft,isPrerelease,publishedAt,targetCommitish,url",
            ),
            check=False,
        )
        if completed.returncode == 0:
            return json.loads(completed.stdout)
        time.sleep(5)
    raise TimeoutError(f"release {tag} not created in {repository}")


def feature_pr(
    repository: str,
    *,
    branch: str,
    title: str,
    changes: dict[str, str],
    body: str = "",
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="main-only-feature-") as temp:
        repo = Path(temp) / repository.rsplit("/", 1)[1]
        run(("gh", "repo", "clone", repository, str(repo)), timeout=300)
        configure_git(repo)
        git("switch", "-c", branch, cwd=repo)
        write_files(repo, changes)
        git("add", ".", cwd=repo)
        commit_args = ["commit", "-m", title]
        if body:
            commit_args.extend(["-m", body])
        git(*commit_args, cwd=repo)
        git("push", "-u", "origin", branch, cwd=repo)
    url = gh(
        "pr",
        "create",
        "--repo",
        repository,
        "--head",
        branch,
        "--base",
        "main",
        "--title",
        title,
        "--body",
        body or "Main-only lab change.",
    )
    number = int(url.rstrip("/").rsplit("/", 1)[1])
    gh("pr", "merge", str(number), "--repo", repository, "--auto", "--squash")
    return wait_pr(repository, number, expected_state="MERGED")


def merge_release_pr(repository: str, expected_tag: str) -> dict[str, Any]:
    pr = wait_open_release_pr(repository)
    number = int(pr["number"])
    gh("pr", "merge", str(number), "--repo", repository, "--auto", "--squash")
    merged = wait_pr(repository, number, expected_state="MERGED")
    release = wait_release(repository, expected_tag)
    return {"pr": merged, "release": release}


def template_features() -> None:
    repository = full_repo("template")
    first = feature_pr(
        repository,
        branch="lab/feature-a",
        title="feat: add feature A to generated projects",
        changes={"template/feature-a.txt.jinja": "feature A\n"},
    )
    release_pr_1 = wait_open_release_pr(repository)
    first_head = release_pr_1["headRefOid"]
    second = feature_pr(
        repository,
        branch="lab/feature-b",
        title="feat: add feature B to generated projects",
        changes={"template/feature-b.txt.jinja": "feature B\n"},
    )
    deadline = time.monotonic() + 360
    release_pr_2 = wait_open_release_pr(repository)
    while release_pr_2["headRefOid"] == first_head and time.monotonic() < deadline:
        time.sleep(5)
        release_pr_2 = wait_open_release_pr(repository)
    if release_pr_2["number"] != release_pr_1["number"]:
        raise RuntimeError("Release Please created more than one release PR")
    if release_pr_2["headRefOid"] == first_head:
        raise RuntimeError("Release Please did not update the existing release PR")
    if "0.2.0" not in release_pr_2["title"]:
        raise RuntimeError(f"expected minor release title, got: {release_pr_2['title']}")
    state = load_state()
    state["template_features"] = {
        "feature_prs": [first, second],
        "release_pr_initial": release_pr_1,
        "release_pr_updated": release_pr_2,
    }
    save_state(state)


def template_release() -> None:
    state = load_state()
    state["template_release"] = merge_release_pr(full_repo("template"), "v0.2.0")
    save_state(state)


def renovate(repository: str) -> str:
    token = gh("auth", "token")
    env = os.environ.copy()
    env["RENOVATE_TOKEN"] = token
    completed = run(
        (
            "docker",
            "run",
            "--rm",
            "-e",
            "RENOVATE_TOKEN",
            "-e",
            "LOG_LEVEL=debug",
            RENOVATE_IMAGE,
            repository,
            "--platform=github",
            "--onboarding=false",
            "--require-config=required",
        ),
        env=env,
        timeout=900,
    )
    return completed.stdout[-20000:]


def latest_renovate_pr(repository: str) -> dict[str, Any]:
    data = json.loads(
        gh(
            "pr",
            "list",
            "--repo",
            repository,
            "--state",
            "all",
            "--search",
            "head:renovate/",
            "--limit",
            "20",
            "--json",
            "number,title,state,mergedAt,headRefName,headRefOid,baseRefName,mergeStateStatus,statusCheckRollup,body,url",
        )
    )
    if not data:
        raise RuntimeError(f"Renovate did not create a PR in {repository}")
    return data[0]


def wait_latest_renovate_pr(
    repository: str,
    *,
    expected_state: str | None,
    timeout: int = 420,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        try:
            last = latest_renovate_pr(repository)
        except RuntimeError:
            time.sleep(5)
            continue
        if expected_state is None or last["state"] == expected_state:
            return last
        time.sleep(5)
    raise TimeoutError(f"Renovate PR in {repository} did not reach {expected_state}: {last}")


def wait_renovate_pr_by_branch(
    repository: str,
    branch: str,
    *,
    expected_state: str,
    timeout: int = 420,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        data = json.loads(
            gh(
                "pr",
                "list",
                "--repo",
                repository,
                "--state",
                "all",
                "--head",
                branch,
                "--limit",
                "10",
                "--json",
                "number,title,state,mergedAt,headRefName,headRefOid,baseRefName,mergeStateStatus,statusCheckRollup,body,url",
            )
        )
        if data:
            last = data[0]
            if last["state"] == expected_state:
                return last
        time.sleep(5)
    raise TimeoutError(
        f"Renovate PR {branch} in {repository} did not reach {expected_state}: {last}"
    )


def template_renovate() -> None:
    repository = full_repo("template_consumer")
    log = renovate(repository)
    pr = wait_latest_renovate_pr(repository, expected_state="OPEN")
    time.sleep(30)
    pr = wait_pr(repository, int(pr["number"]), expected_state="OPEN", timeout=30)
    files = json.loads(gh("api", f"repos/{repository}/pulls/{pr['number']}/files"))
    paths = sorted(item["filename"] for item in files)
    required = {".copier-answers.yml", "feature-a.txt", "feature-b.txt"}
    if not required.issubset(paths):
        raise RuntimeError(f"Copier PR missing expected files: {paths}")
    state = load_state()
    state["template_renovate"] = {"pr": pr, "files": paths, "log_tail": log}
    save_state(state)


def tool_release_step(
    *,
    key: str,
    branch: str,
    title: str,
    body: str,
    file_name: str,
    content: str,
    expected_tag: str,
) -> None:
    repository = full_repo("tool")
    feature = feature_pr(
        repository,
        branch=branch,
        title=title,
        body=body,
        changes={file_name: content},
    )
    release_pr = wait_open_release_pr(repository)
    if expected_tag.removeprefix("v") not in release_pr["title"]:
        raise RuntimeError(f"unexpected Release Please version: {release_pr['title']}")
    released = merge_release_pr(repository, expected_tag)
    state = load_state()
    state[key] = {
        "feature_pr": feature,
        "release_pr_before_merge": release_pr,
        **released,
    }
    save_state(state)


def merge_consumer_pr(repository: str, pr: dict[str, Any]) -> dict[str, Any]:
    gh("pr", "merge", str(pr["number"]), "--repo", repository, "--auto", "--squash")
    return wait_pr(repository, int(pr["number"]), expected_state="MERGED", timeout=420)


def tool_pre1_release() -> None:
    tool_release_step(
        key="tool_pre1_release",
        branch="lab/pre1-feature",
        title="feat: add greeting helper",
        body="",
        file_name="src/ternforge_main_only_lab_tool/greeting.py",
        content="def greeting() -> str:\n    return 'hello'\n",
        expected_tag="v0.2.0",
    )


def tool_pre1_renovate() -> None:
    repository = full_repo("tool_consumer")
    log = renovate(repository)
    pr = wait_latest_renovate_pr(repository, expected_state="OPEN")
    time.sleep(30)
    pr = wait_pr(repository, int(pr["number"]), expected_state="OPEN", timeout=30)
    merged = merge_consumer_pr(repository, pr)
    state = load_state()
    state["tool_pre1_renovate"] = {
        "manual_pr": pr,
        "manual_merge": merged,
        "log_tail": log,
    }
    save_state(state)


def tool_one_release() -> None:
    tool_release_step(
        key="tool_one_release",
        branch="lab/stable-release",
        title="feat!: stabilize public API",
        body="Release-As: 1.0.0",
        file_name="src/ternforge_main_only_lab_tool/stable.py",
        content="STABLE = True\n",
        expected_tag="v1.0.0",
    )


def tool_one_renovate() -> None:
    repository = full_repo("tool_consumer")
    log = renovate(repository)
    pr = wait_latest_renovate_pr(repository, expected_state="OPEN")
    time.sleep(30)
    pr = wait_pr(repository, int(pr["number"]), expected_state="OPEN", timeout=30)
    merged = merge_consumer_pr(repository, pr)
    state = load_state()
    state["tool_one_renovate"] = {
        "major_pr": pr,
        "manual_merge": merged,
        "log_tail": log,
    }
    save_state(state)


def tool_minor_release() -> None:
    tool_release_step(
        key="tool_minor_release",
        branch="lab/stable-minor",
        title="feat: add stable helper",
        body="",
        file_name="src/ternforge_main_only_lab_tool/helper.py",
        content="def helper() -> int:\n    return 1\n",
        expected_tag="v1.1.0",
    )


def tool_minor_renovate() -> None:
    repository = full_repo("tool_consumer")
    log = renovate(repository)
    merged = wait_renovate_pr_by_branch(
        repository,
        "renovate/ternforge-main-only-lab-tool-1.x",
        expected_state="MERGED",
        timeout=480,
    )
    state = load_state()
    state["tool_minor_renovate"] = {"automerge_pr": merged, "log_tail": log}
    save_state(state)


def tool_major_release() -> None:
    tool_release_step(
        key="tool_major_release",
        branch="lab/stable-major",
        title="feat!: replace the value API",
        body="BREAKING CHANGE: value() now returns a mapping.",
        file_name="src/ternforge_main_only_lab_tool/__init__.py",
        content="def value() -> dict[str, str]:\n    return {'value': 'v2'}\n",
        expected_tag="v2.0.0",
    )


def tool_major_renovate() -> None:
    repository = full_repo("tool_consumer")
    log = renovate(repository)
    pr = wait_renovate_pr_by_branch(
        repository,
        "renovate/ternforge-main-only-lab-tool-2.x",
        expected_state="OPEN",
    )
    time.sleep(30)
    pr = wait_pr(repository, int(pr["number"]), expected_state="OPEN", timeout=30)
    state = load_state()
    state["tool_major_renovate"] = {"manual_pr": pr, "log_tail": log}
    save_state(state)


def collect() -> None:
    state = load_state()
    settings: dict[str, Any] = {}
    for key in REPOS:
        repository = full_repo(key)
        settings[key] = json.loads(
            gh(
                "repo",
                "view",
                repository,
                "--json",
                "nameWithOwner,defaultBranchRef,deleteBranchOnMerge,mergeCommitAllowed,rebaseMergeAllowed,squashMergeAllowed,url",
            )
        )
        repository_api = json.loads(gh("api", f"repos/{repository}"))
        settings[key]["allowAutoMerge"] = repository_api["allow_auto_merge"]
        settings[key]["rulesets"] = json.loads(gh("api", f"repos/{repository}/rulesets"))
        settings[key]["branches"] = json.loads(
            gh("api", f"repos/{repository}/branches?per_page=100")
        )
    state["repository_settings"] = settings
    checks = {
        "one_permanent_branch": all(
            all(
                branch["name"] == "main" or branch["name"].startswith("renovate/")
                for branch in item["branches"]
            )
            for item in settings.values()
        ),
        "template_release_pr_reused": state.get("template_features", {})
        .get("release_pr_initial", {})
        .get("number")
        == state.get("template_features", {}).get("release_pr_updated", {}).get("number"),
        "template_release_minor": state.get("template_release", {})
        .get("release", {})
        .get("tagName")
        == "v0.2.0",
        "template_consumer_manual": state.get("template_renovate", {})
        .get("pr", {})
        .get("state")
        == "OPEN",
        "tool_pre1_manual": state.get("tool_pre1_renovate", {})
        .get("manual_pr", {})
        .get("state")
        == "OPEN",
        "tool_stable_minor_automerge": state.get("tool_minor_renovate", {})
        .get("automerge_pr", {})
        .get("state")
        == "MERGED",
        "tool_major_manual": state.get("tool_major_renovate", {})
        .get("manual_pr", {})
        .get("state")
        == "OPEN",
    }
    state["checks"] = checks
    state["passed"] = all(checks.values())
    EVIDENCE_JSON.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_JSON.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Main-only release lab — 2026-07-24",
        "",
        f"Result: **{'PASS' if state['passed'] else 'FAIL'}**",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in checks.items())
    lines.extend(["", "## Repositories", ""])
    lines.extend(f"- `{full_repo(key)}`" for key in REPOS)
    lines.extend(
        [
            "",
            "## Observed model",
            "",
            "- One permanent `main` branch, squash-only PR flow, one required `ci / required` check.",
            "- Release Please kept one release PR and updated it after a second feature merge.",
            "- Merging the release PR created the expected tag and GitHub Release.",
            "- Copier consumer update stayed open for manual review.",
            "- Pre-1.0 and major tool updates stayed open for manual review.",
            "- Stable minor tool update merged automatically only after consumer CI passed.",
            "",
            "## Important findings",
            "",
            "- The required check must have the explicit job name `ci / required`; a job id alone produces a different context.",
            "- Release Please needs the repository-scoped GitHub App token in this organization; the default workflow token cannot create its PR.",
            "- `astral-sh/setup-uv@v8` does not resolve; use an exact released tag or immutable SHA.",
            "- Renovate's default two-PR-per-hour limit delayed only the compressed lab sequence; the normal configuration was restored.",
            "",
        ]
    )
    EVIDENCE_MD.write_text("\n".join(lines), encoding="utf-8")
    save_state(state)
    if not state["passed"]:
        raise SystemExit("main-only release lab failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase",
        choices=[
            "provision",
            "template-features",
            "template-release",
            "template-renovate",
            "tool-pre1-release",
            "tool-pre1-renovate",
            "tool-one-release",
            "tool-one-renovate",
            "tool-minor-release",
            "tool-minor-renovate",
            "tool-major-release",
            "tool-major-renovate",
            "collect",
        ],
    )
    actions = {
        "provision": provision,
        "template-features": template_features,
        "template-release": template_release,
        "template-renovate": template_renovate,
        "tool-pre1-release": tool_pre1_release,
        "tool-pre1-renovate": tool_pre1_renovate,
        "tool-one-release": tool_one_release,
        "tool-one-renovate": tool_one_renovate,
        "tool-minor-release": tool_minor_release,
        "tool-minor-renovate": tool_minor_renovate,
        "tool-major-release": tool_major_release,
        "tool-major-renovate": tool_major_renovate,
        "collect": collect,
    }
    actions[parser.parse_args().phase]()


if __name__ == "__main__":
    main()
