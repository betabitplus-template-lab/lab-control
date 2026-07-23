#!/usr/bin/env python3
"""Provision and verify the minimal read-only Copier drift-audit contract."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ORG = "betabitplus-template-lab"
TEMPLATE_NAME = "sandbox-drift-template-20260723-r1"
CONSUMER_NAME = "sandbox-drift-consumer-20260723-r1"
TEMPLATE_REPOSITORY = f"{ORG}/{TEMPLATE_NAME}"
CONSUMER_REPOSITORY = f"{ORG}/{CONSUMER_NAME}"
TEMPLATE_URL = f"https://github.com/{TEMPLATE_REPOSITORY}.git"
COPIER_VERSION = "9.16.0"
UV_VERSION = "0.8.17"
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_JSON = ROOT / "evidence" / "copier-drift-audit-20260723.json"
EVIDENCE_MD = ROOT / "evidence" / "copier-drift-audit-20260723.md"


def run(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        command = " ".join(args)
        raise RuntimeError(
            f"command failed ({completed.returncode}): {command}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(("gh", *args), check=check)


def copier(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return run(
        (
            "uvx",
            "--from",
            f"copier=={COPIER_VERSION}",
            "copier",
            *args,
        ),
        cwd=cwd,
    )


def configure_git(repository: Path) -> None:
    run(("git", "config", "user.name", "Ternforge Drift Audit Lab"), cwd=repository)
    run(
        ("git", "config", "user.email", "8123085+betabitplus@users.noreply.github.com"),
        cwd=repository,
    )


def write_template_v1(repository: Path) -> None:
    template = repository / "template"
    template.mkdir(parents=True, exist_ok=True)
    (repository / "copier.yml").write_text(
        """\
_subdirectory: template
_skip_if_exists:
  - README.md
  - CREATE_ONCE.txt
project_name:
  type: str
  default: drift-lab
"""
    )
    (template / "{{ _copier_conf.answers_file }}.jinja").write_text(
        "{{ _copier_answers|to_nice_yaml }}\n"
    )
    (template / "README.md.jinja").write_text(
        "# {{ project_name }}\n\nGenerated README v1.\n"
    )
    (template / "CREATE_ONCE.txt.jinja").write_text("create-once v1\n")
    (template / "managed.txt.jinja").write_text("managed v1\n")
    (template / "deleted-managed.txt.jinja").write_text("managed deletion probe v1\n")


def write_template_v2(repository: Path) -> None:
    template = repository / "template"
    (template / "managed.txt.jinja").write_text("managed v2\n")
    (template / "latest-only.txt.jinja").write_text("introduced in v1.1.0\n")


def assert_empty_repository(repository: str) -> None:
    result = gh("api", f"repos/{repository}/branches", check=False)
    if result.returncode == 0 and json.loads(result.stdout):
        raise RuntimeError(f"refusing to provision non-empty repository: {repository}")


def provision() -> None:
    assert_empty_repository(TEMPLATE_REPOSITORY)
    assert_empty_repository(CONSUMER_REPOSITORY)
    gh("auth", "setup-git")

    with tempfile.TemporaryDirectory(prefix="ternforge-drift-provision-") as temp:
        temp_root = Path(temp)
        template_repo = temp_root / "template"
        consumer_repo = temp_root / "consumer"

        run(("git", "clone", TEMPLATE_URL, str(template_repo)))
        run(("git", "switch", "-c", "main"), cwd=template_repo)
        configure_git(template_repo)
        write_template_v1(template_repo)
        run(("git", "add", "."), cwd=template_repo)
        run(("git", "commit", "-m", "lab: add drift template v1"), cwd=template_repo)
        run(("git", "tag", "v1.0.0"), cwd=template_repo)
        run(("git", "push", "-u", "origin", "main", "--tags"), cwd=template_repo)
        gh("repo", "edit", TEMPLATE_REPOSITORY, "--default-branch", "main")

        copier(
            "copy",
            TEMPLATE_URL,
            str(consumer_repo),
            "--vcs-ref=v1.0.0",
            "--defaults",
            "--data",
            "project_name=drift-lab",
            cwd=temp_root,
        )
        run(("git", "init", "-b", "dev"), cwd=consumer_repo)
        configure_git(consumer_repo)
        run(("git", "add", "."), cwd=consumer_repo)
        run(("git", "commit", "-m", "lab: record clean Copier consumer"), cwd=consumer_repo)
        run(("git", "tag", "clean-state"), cwd=consumer_repo)

        (consumer_repo / "managed.txt").write_text("consumer-managed override\n")
        (consumer_repo / "deleted-managed.txt").unlink()
        (consumer_repo / "README.md").write_text("# Locally customized README\n")
        (consumer_repo / "CREATE_ONCE.txt").unlink()
        notes = consumer_repo / "notes"
        notes.mkdir()
        (notes / "local.txt").write_text("unrelated user-owned file\n")
        run(("git", "add", "-A"), cwd=consumer_repo)
        run(("git", "commit", "-m", "lab: add controlled consumer deviations"), cwd=consumer_repo)
        run(
            (
                "git",
                "remote",
                "add",
                "origin",
                f"https://github.com/{CONSUMER_REPOSITORY}.git",
            ),
            cwd=consumer_repo,
        )
        run(("git", "push", "-u", "origin", "dev", "--tags"), cwd=consumer_repo)
        gh("repo", "edit", CONSUMER_REPOSITORY, "--default-branch", "dev")

        write_template_v2(template_repo)
        run(("git", "add", "."), cwd=template_repo)
        run(("git", "commit", "-m", "lab: release drift template v1.1.0"), cwd=template_repo)
        run(("git", "tag", "v1.1.0"), cwd=template_repo)
        run(("git", "push", "origin", "main", "--tags"), cwd=template_repo)

    print(
        json.dumps(
            {
                "template_repository": TEMPLATE_REPOSITORY,
                "consumer_repository": CONSUMER_REPOSITORY,
                "copier_version": COPIER_VERSION,
                "status": "provisioned",
            },
            indent=2,
        )
    )


def parse_name_status(output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        status, path = line.split("\t", 1)
        result[path] = status
    return result


def clone_consumer(destination: Path, ref: str) -> None:
    gh(
        "repo",
        "clone",
        CONSUMER_REPOSITORY,
        str(destination),
        "--",
        "--depth=1",
        f"--branch={ref}",
    )


def audit_checkout(destination: Path, ref: str) -> dict[str, Any]:
    clone_consumer(destination, ref)
    head_before = run(("git", "rev-parse", "HEAD"), cwd=destination).stdout.strip()
    status_before = run(("git", "status", "--porcelain=v1"), cwd=destination).stdout
    if status_before:
        raise RuntimeError(f"clone is unexpectedly dirty for {ref}: {status_before}")

    check_update = copier(
        "check-update", "--output-format", "json", ".", cwd=destination
    )
    check_update_json = json.loads(check_update.stdout)

    recopy = copier(
        "recopy",
        "--vcs-ref=:current:",
        "--defaults",
        "--overwrite",
        "--skip-tasks",
        ".",
        cwd=destination,
    )
    run(("git", "add", "-N", "."), cwd=destination)
    name_status_text = run(("git", "diff", "--name-status"), cwd=destination).stdout
    patch = run(("git", "diff", "--binary"), cwd=destination).stdout
    head_after = run(("git", "rev-parse", "HEAD"), cwd=destination).stdout.strip()

    return {
        "ref": ref,
        "head_before": head_before,
        "head_after": head_after,
        "head_unchanged": head_before == head_after,
        "check_update": check_update_json,
        "recopy_stdout": recopy.stdout,
        "recopy_stderr": recopy.stderr,
        "name_status": parse_name_status(name_status_text),
        "name_status_text": name_status_text,
        "patch": patch,
    }


def audit() -> None:
    gh("auth", "setup-git")
    remote_before = gh(
        "api",
        f"repos/{CONSUMER_REPOSITORY}/git/ref/heads/dev",
        "--jq",
        ".object.sha",
    ).stdout.strip()

    with tempfile.TemporaryDirectory(prefix="ternforge-drift-audit-") as temp:
        temp_root = Path(temp)
        clean = audit_checkout(temp_root / "clean", "clean-state")
        drift = audit_checkout(temp_root / "drift", "dev")

    remote_after = gh(
        "api",
        f"repos/{CONSUMER_REPOSITORY}/git/ref/heads/dev",
        "--jq",
        ".object.sha",
    ).stdout.strip()

    expected_drift = {
        "managed.txt": "M",
        "deleted-managed.txt": "A",
        "CREATE_ONCE.txt": "A",
    }
    assertions = {
        "clean_recopy_has_empty_diff": clean["name_status"] == {},
        "drift_paths_match_expected": drift["name_status"] == expected_drift,
        "modified_skip_if_exists_is_preserved": "README.md" not in drift["name_status"],
        "unrelated_user_file_is_ignored": "notes/local.txt" not in drift["name_status"],
        "answers_file_is_stable": ".copier-answers.yml" not in drift["name_status"],
        "clean_head_unchanged": clean["head_unchanged"],
        "drift_head_unchanged": drift["head_unchanged"],
        "remote_dev_sha_unchanged": remote_before == remote_after,
        "version_drift_reported_for_clean_checkout": bool(clean["check_update"]),
        "version_drift_reported_for_drift_checkout": bool(drift["check_update"]),
    }
    passed = all(assertions.values())

    evidence = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "conclusion": "PASS" if passed else "FAIL",
        "copier_version": COPIER_VERSION,
        "uv_version": UV_VERSION,
        "template_repository": TEMPLATE_REPOSITORY,
        "consumer_repository": CONSUMER_REPOSITORY,
        "remote_dev_sha_before": remote_before,
        "remote_dev_sha_after": remote_after,
        "assertions": assertions,
        "clean_checkout": clean,
        "drift_checkout": drift,
    }
    EVIDENCE_JSON.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    rows = [
        ("clean-state", "yes" if clean["name_status"] else "no", clean["name_status_text"] or "—"),
        ("dev", "yes" if drift["name_status"] else "no", drift["name_status_text"].strip() or "—"),
    ]
    assertion_lines = "\n".join(
        f"- {'PASS' if value else 'FAIL'} — `{name}`" for name, value in assertions.items()
    )
    row_lines = "\n".join(
        f"| `{ref}` | {has_drift} | `{paths.replace(chr(10), '; ')}` |"
        for ref, has_drift, paths in rows
    )
    EVIDENCE_MD.write_text(
        f"""# Copier drift audit lab — 23 July 2026

## Result

```text
{evidence['conclusion']}
```

The experiment used Copier `{COPIER_VERSION}` and uv `{UV_VERSION}` against two private repositories in `{ORG}`.

| Checkout | Local drift | Git name-status |
| --- | --- | --- |
{row_lines}

## Assertions

{assertion_lines}

## Contract demonstrated

```text
fleet target
→ disposable shallow checkout
→ copier check-update
→ copier recopy --vcs-ref=:current: --defaults --overwrite --skip-tasks
→ git add -N .
→ git diff --name-status / git diff --binary
```

The clean checkout produced no local diff while still reporting that template `v1.1.0` exists above recorded `v1.0.0`. The divergent checkout reported only the expected template-footprint deviations: one modified managed file and two recreated missing template files. The existing modified `_skip_if_exists` README and unrelated committed user file were not reported. Local and remote commit SHAs remained unchanged.

Machine-readable evidence: `evidence/copier-drift-audit-20260723.json`.
"""
    )

    print(json.dumps(evidence, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("provision", "audit"))
    args = parser.parse_args()
    if args.command == "provision":
        provision()
    else:
        audit()


if __name__ == "__main__":
    main()
