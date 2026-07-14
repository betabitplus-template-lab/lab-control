#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ORG = "betabitplus-template-lab"
ALLOWED = {
    f"{ORG}/python-lib",
    f"{ORG}/python-internal-package",
    f"{ORG}/python-starter-platform",
}
TAG_RE = re.compile(r"^v\d+\.\d+\.\d+(?:[a-z]+\d+)?$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def run(*args: str, cwd: Path | None = None, capture: bool = False, check: bool = True):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=capture, check=check)


def out(*args: str, cwd: Path | None = None) -> str:
    return run(*args, cwd=cwd, capture=True).stdout.strip()


def main() -> None:
    token = os.environ["LAB_TOKEN"]
    root = Path(os.environ.get("GITHUB_WORKSPACE", "."))
    request = json.loads((root / "release" / "request.json").read_text(encoding="utf-8"))
    releases = request.get("releases", [])
    if not isinstance(releases, list):
        raise SystemExit("releases must be a list")
    results = []
    run("git", "config", "--global", "user.name", "Template Lab Release Bot")
    run("git", "config", "--global", "user.email", "8123085+betabitplus@users.noreply.github.com")
    run(
        "git",
        "config",
        "--global",
        f"url.https://x-access-token:{token}@github.com/.insteadOf",
        "https://github.com/",
    )
    with tempfile.TemporaryDirectory(prefix="release-lab-") as td:
        for item in releases:
            repository = item.get("repository")
            commit = item.get("commit")
            tag = item.get("tag")
            if repository not in ALLOWED:
                raise SystemExit(f"unsafe repository: {repository}")
            if not isinstance(commit, str) or not SHA_RE.fullmatch(commit):
                raise SystemExit(f"invalid commit for {repository}: {commit}")
            if not isinstance(tag, str) or not TAG_RE.fullmatch(tag):
                raise SystemExit(f"invalid tag for {repository}: {tag}")
            repo = Path(td) / repository.rsplit("/", 1)[1]
            run("git", "clone", "--no-checkout", f"https://github.com/{repository}.git", str(repo))
            run("git", "fetch", "origin", "main", "--tags", cwd=repo)
            main_sha = out("git", "rev-parse", "origin/main", cwd=repo)
            if main_sha != commit:
                raise SystemExit(f"release race for {repository}: request={commit}, main={main_sha}")
            existing = run("git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{}}", cwd=repo, capture=True, check=False)
            if existing.returncode == 0:
                if existing.stdout.strip() != commit:
                    raise SystemExit(f"tag {tag} already points elsewhere in {repository}")
                results.append({"repository": repository, "tag": tag, "commit": commit, "created": False})
                continue
            run("git", "tag", "-a", tag, commit, "-m", f"{repository.rsplit('/', 1)[1]} {tag}", cwd=repo)
            run("git", "push", "origin", f"refs/tags/{tag}", cwd=repo)
            results.append({"repository": repository, "tag": tag, "commit": commit, "created": True})
    result_path = root / "docs" / "results" / "release.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps({"releases": results}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
