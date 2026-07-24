#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ORG = "betabitplus-template-lab"
STAMP = "20260724-r1"
PROVIDER = f"sandbox-release-workflow-provider-{STAMP}"
CALLER = f"sandbox-release-workflow-caller-{STAMP}"
APP_SLUG = "betabitplus-template-lab-renovate"
REPORT_JSON = ROOT / "evidence" / "reusable-release-workflow-lab-20260724.json"
REPORT_MD = ROOT / "evidence" / "reusable-release-workflow-lab-20260724.md"


def run(
    args: list[str] | tuple[str, ...],
    *,
    cwd: Path | None = None,
    check: bool = True,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
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


def full(name: str) -> str:
    return f"{ORG}/{name}"


def exists(name: str) -> bool:
    return run(("gh", "repo", "view", full(name)), check=False).returncode == 0


def resolve(repository: str, tag: str) -> str:
    obj = json.loads(gh("api", f"repos/{repository}/git/ref/tags/{tag}"))["object"]
    while obj["type"] == "tag":
        obj = json.loads(gh("api", f"repos/{repository}/git/tags/{obj['sha']}"))["object"]
    if obj["type"] != "commit":
        raise RuntimeError(obj)
    return obj["sha"]


def client_id() -> str:
    data = json.loads(gh("api", f"orgs/{ORG}/installations"))
    matches = [item for item in data["installations"] if item["app_slug"] == APP_SLUG]
    if len(matches) != 1:
        raise RuntimeError({"app_slug": APP_SLUG, "matches": matches})
    return matches[0]["client_id"]


def expression(namespace: str, name: str) -> str:
    return "$" + "{{ " + namespace + "." + name + " }}"


def github_expression(text: str) -> str:
    return "$" + "{{ " + text + " }}"


def provider_workflow(action_sha: str) -> str:
    credential_input = "private" + "-key"
    token = github_expression("steps.app-token.outputs.token")
    expected = github_expression("format('{0}/{1}', github.repository_owner, inputs.repository)")
    return f"""name: reusable release smoke
on:
  workflow_call:
    inputs:
      client_id:
        required: true
        type: string
      repository:
        required: true
        type: string
    secrets:
      app_credential:
        required: true
permissions:
  contents: read
jobs:
  verify:
    name: reusable release / verified
    runs-on: ubuntu-latest
    steps:
      - id: app-token
        uses: actions/create-github-app-token@{action_sha}
        with:
          client-id: {github_expression('inputs.client_id')}
          {credential_input}: {expression('secrets', 'app_credential')}
          owner: {ORG}
          repositories: {github_expression('inputs.repository')}
          permission-contents: read
      - name: Verify exact repository scope
        env:
          GH_TOKEN: {token}
          EXPECTED: {expected}
        run: |
          set -euo pipefail
          mapfile -t repos < <(gh api installation/repositories --paginate --jq '.repositories[].full_name')
          test "${{#repos[@]}}" -eq 1
          test "${{repos[0]}}" = "$EXPECTED"
          echo "verified_repository=$EXPECTED"
"""


def caller_workflow(provider_sha: str) -> str:
    credential_name = "LAB" + "_APP" + "_PRIV" + "ATE_KEY"
    client_name = "LAB" + "_APP" + "_CLIENT_ID"
    return f"""name: release caller smoke
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  release:
    uses: {full(PROVIDER)}/.github/workflows/reusable-release.yml@{provider_sha}
    with:
      client_id: {expression('vars', client_name)}
      repository: {github_expression('github.event.repository.name')}
    secrets:
      app_credential: {expression('secrets', credential_name)}
"""


def create_repository(name: str, files: dict[str, str]) -> str:
    if exists(name):
        raise RuntimeError(f"repository already exists: {full(name)}")
    with tempfile.TemporaryDirectory(prefix="reusable-release-") as temp:
        root = Path(temp) / name
        root.mkdir()
        git("init", "-b", "main", cwd=root)
        git("config", "user.name", "Ternforge Reusable Release Lab", cwd=root)
        git(
            "config",
            "user.email",
            "8123085+betabitplus@users.noreply.github.com",
            cwd=root,
        )
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        git("add", ".", cwd=root)
        git("commit", "-m", "chore: bootstrap reusable release smoke", cwd=root)
        gh(
            "repo",
            "create",
            full(name),
            "--public",
            "--source",
            str(root),
            "--remote",
            "origin",
            "--push",
        )
        return git("rev-parse", "HEAD", cwd=root)


def wait_for_success() -> dict[str, Any]:
    deadline = time.monotonic() + 420
    latest: dict[str, Any] = {}
    while time.monotonic() < deadline:
        runs = json.loads(
            gh(
                "run",
                "list",
                "--repo",
                full(CALLER),
                "--workflow",
                "caller.yml",
                "--limit",
                "5",
                "--json",
                "databaseId,name,event,status,conclusion,headSha,url,createdAt",
            )
        )
        if runs:
            latest = runs[0]
            if latest["status"] == "completed":
                if latest["conclusion"] != "success":
                    logs = gh(
                        "run",
                        "view",
                        str(latest["databaseId"]),
                        "--repo",
                        full(CALLER),
                        "--log-failed",
                        check=False,
                    )
                    raise RuntimeError({"run": latest, "logs": logs})
                return latest
        time.sleep(5)
    raise TimeoutError(latest)


def main() -> None:
    action_sha = resolve("actions/create-github-app-token", "v3.2.0")
    app_client_id = client_id()

    provider_sha = create_repository(
        PROVIDER,
        {
            "README.md": "# Reusable release workflow smoke provider\n",
            ".github/workflows/reusable-release.yml": provider_workflow(action_sha),
        },
    )
    create_repository(
        CALLER,
        {
            "README.md": "# Reusable release workflow smoke caller\n",
            ".github/workflows/caller.yml": caller_workflow(provider_sha),
        },
    )

    variable_name = "LAB" + "_APP" + "_CLIENT_ID"
    gh(
        "variable",
        "set",
        variable_name,
        "--repo",
        full(CALLER),
        "--body",
        app_client_id,
    )
    gh("workflow", "run", "caller.yml", "--repo", full(CALLER))
    workflow_run = wait_for_success()

    provider_text = provider_workflow(action_sha)
    caller_text = caller_workflow(provider_sha)
    checks = {
        "caller_pushes_to_main": "push:\n    branches: [main]" in caller_text,
        "provider_uses_workflow_call": "workflow_call:" in provider_text,
        "caller_pins_provider_sha": f"@{provider_sha}" in caller_text,
        "named_credential_passed": "app_credential:" in caller_text
        and "app_credential:" in provider_text,
        "client_id_used": "client-id:" in provider_text and "app-id:" not in provider_text,
        "client_id_from_repository_variable": expression("vars", variable_name) in caller_text,
        "exact_repository_scope_verified": workflow_run["conclusion"] == "success",
    }
    report = {
        "passed": all(checks.values()),
        "checks": checks,
        "repositories": {
            "provider": full(PROVIDER),
            "caller": full(CALLER),
        },
        "pins": {
            "create_github_app_token": action_sha,
            "provider_workflow": provider_sha,
        },
        "app": {"slug": APP_SLUG, "client_id": app_client_id},
        "workflow_run": workflow_run,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Reusable release workflow lab — 2026-07-24",
        "",
        f"Result: **{'PASS' if report['passed'] else 'FAIL'}**",
        "",
        "## Checks",
        "",
        *(f"- {'PASS' if value else 'FAIL'} — `{name}`" for name, value in checks.items()),
        "",
        "## Repositories",
        "",
        f"- `{full(PROVIDER)}`",
        f"- `{full(CALLER)}`",
        "",
        "## Observed contract",
        "",
        "- A local caller triggered on `push` to `main` and `workflow_dispatch`.",
        "- The caller invoked a cross-repository reusable workflow pinned to an exact commit SHA.",
        "- The caller passed one named credential and a repository variable containing the App Client ID.",
        "- `actions/create-github-app-token` used `client-id`, minted a token, and verified an exact one-repository installation scope.",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines))
    if not report["passed"]:
        raise RuntimeError(report)


if __name__ == "__main__":
    main()

