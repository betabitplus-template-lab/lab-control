#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pilot


def safe_run(
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = [str(arg) for arg in args]
    display = [
        re.sub(r"x-access-token:[^@]+@", "x-access-token:<redacted>@", part)
        for part in cmd
    ]
    print("+", " ".join(display), flush=True)
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=capture,
        check=check,
    )


def clean_repo(repo: Path) -> None:
    pilot.git(repo, "submodule", "deinit", "-f", "--all", check=False)
    pilot.git(
        repo,
        "rm",
        "-f",
        "--ignore-unmatch",
        "template/_components",
        ".gitmodules",
        check=False,
    )
    for child in repo.iterdir():
        if child.name in {".git", ".github"}:
            continue
        pilot.safe_rmtree(child)


pilot.run = safe_run
pilot.clean_repo = clean_repo
pilot.prepare()
