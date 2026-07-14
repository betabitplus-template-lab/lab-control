#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", "."))


def run(*args: str, cwd: Path | None = None, check: bool = True, capture: bool = False):
    return subprocess.run(args, cwd=cwd, check=check, text=True, capture_output=capture)


def write(path: Path, text: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def git(repo: Path, *args: str, check: bool = True, capture: bool = False):
    return run("git", *args, cwd=repo, check=check, capture=capture)


def commit(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)


def executable(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


def make_template(root: Path) -> Path:
    template = root / "template-source"
    template.mkdir()
    git(template, "init", "-b", "main")
    git(template, "config", "user.name", "acceptance")
    git(template, "config", "user.email", "acceptance@example.invalid")

    copier_v1 = """_min_copier_version: \"9.16.0\"\n_subdirectory: template\n_answers_file: .copier-answers.yml\n_templates_suffix: \"\"\n_skip_if_exists:\n  - user-owned/**\nproject_name:\n  type: str\n  default: sample\n"""
    write(template / "copier.yml", copier_v1)
    write(template / "template" / "separate.txt", "template-v1\n")
    write(template / "template" / "mixed.txt", "template-head-v1\nstable-middle\nuser-tail-v1\n")
    write(template / "template" / "conflict.txt", "shared-line-v1\n")
    write(template / "template" / "removed.txt", "remove-me\n")
    write(template / "template" / "renamed-old.txt", "rename-me\n")
    write(template / "template" / "mode.sh", "#!/usr/bin/env bash\necho v1\n", 0o644)
    write(template / "template" / "user-owned" / "seed.txt", "template seed\n")
    commit(template, "template v1")
    git(template, "tag", "v0.1.0")

    copier_v2 = copier_v1 + "feature_name:\n  type: str\n  default: enabled\n"
    write(template / "copier.yml", copier_v2)
    write(template / "template" / "separate.txt", "template-v2\n")
    write(template / "template" / "mixed.txt", "template-head-v2\nstable-middle\nuser-tail-v1\n")
    write(template / "template" / "conflict.txt", "shared-line-template-v2\n")
    (template / "template" / "removed.txt").unlink()
    (template / "template" / "renamed-old.txt").rename(template / "template" / "renamed-new.txt")
    write(template / "template" / "new.txt", "new-file\n")
    write(template / "template" / "mode.sh", "#!/usr/bin/env bash\necho v2\n", 0o755)
    write(template / "template" / "user-owned" / "seed.txt", "template seed v2\n")
    commit(template, "template v2")
    git(template, "tag", "v0.2.0")

    copier_v3 = copier_v2 + "required_without_default:\n  type: str\n"
    write(template / "copier.yml", copier_v3)
    commit(template, "template v3 required question")
    git(template, "tag", "v0.3.0")
    return template


def copy_at(template: Path, destination: Path, ref: str = "v0.1.0") -> None:
    run("copier", "copy", "--defaults", "--vcs-ref", ref, str(template), str(destination))
    git(destination, "init", "-b", "main")
    git(destination, "config", "user.name", "downstream")
    git(destination, "config", "user.email", "downstream@example.invalid")
    commit(destination, "initial generated state")


def update(destination: Path, ref: str, check: bool = True):
    return run(
        "copier",
        "update",
        "--skip-answered",
        "--defaults",
        "--answers-file",
        ".copier-answers.yml",
        "--vcs-ref",
        ref,
        cwd=destination,
        check=check,
        capture=True,
    )


def main() -> None:
    results: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="copier-matrix-") as td:
        root = Path(td)
        template = make_template(root)

        clean = root / "clean"
        copy_at(template, clean)
        write(clean / "unrelated-user.txt", "preserve\n")
        write(clean / "mixed.txt", "template-head-v1\nstable-middle\nuser-tail-local\n")
        write(clean / "user-owned" / "seed.txt", "user replacement\n")
        commit(clean, "user changes")
        update(clean, "v0.2.0")
        results["clean_update"] = (clean / "separate.txt").read_text() == "template-v2\n"
        results["unrelated_user_file_preserved"] = (clean / "unrelated-user.txt").read_text() == "preserve\n"
        results["mixed_nonconflict_preserved"] = (clean / "mixed.txt").read_text() == "template-head-v2\nstable-middle\nuser-tail-local\n"
        results["skip_if_exists_preserved"] = (clean / "user-owned" / "seed.txt").read_text() == "user replacement\n"
        results["new_file"] = (clean / "new.txt").is_file()
        results["deleted_file"] = not (clean / "removed.txt").exists()
        results["rename"] = not (clean / "renamed-old.txt").exists() and (clean / "renamed-new.txt").is_file()
        results["executable_bit_update"] = executable(clean / "mode.sh") if os.name != "nt" else True
        answers = (clean / ".copier-answers.yml").read_text(encoding="utf-8")
        results["answers_updated"] = "v0.2.0" in answers
        results["new_question_with_default"] = "feature_name" in answers

        conflict = root / "conflict"
        copy_at(template, conflict)
        write(conflict / "conflict.txt", "shared-line-user\n")
        commit(conflict, "user conflict")
        conflict_run = update(conflict, "v0.2.0", check=False)
        conflict_text = (conflict / "conflict.txt").read_text(encoding="utf-8")
        results["true_conflict_markers"] = all(marker in conflict_text for marker in ("<<<<<<<", "=======", ">>>>>>>"))
        results["conflict_command_completed"] = conflict_run.returncode == 0

        required = root / "required"
        copy_at(template, required)
        required_run = update(required, "v0.3.0", check=False)
        results["required_question_without_default_fails"] = required_run.returncode != 0

        workspace = root / "workspace"
        workspace.mkdir()
        git(workspace, "init", "-b", "main")
        git(workspace, "config", "user.name", "workspace")
        git(workspace, "config", "user.email", "workspace@example.invalid")
        for name in ("runtime", "tooling"):
            run("copier", "copy", "--defaults", "--vcs-ref", "v0.1.0", str(template), str(workspace / "packages" / name))
        commit(workspace, "two Copier relationships")
        for name in ("runtime", "tooling"):
            update(workspace / "packages" / name, "v0.2.0")
        nested = list(workspace.rglob(".copier-answers.yml"))
        results["nested_answers_count"] = len(nested)
        results["nested_answers_updated"] = len(nested) == 2 and all("v0.2.0" in path.read_text(encoding="utf-8") for path in nested)

    expected_true = [
        "clean_update",
        "unrelated_user_file_preserved",
        "mixed_nonconflict_preserved",
        "skip_if_exists_preserved",
        "new_file",
        "deleted_file",
        "rename",
        "executable_bit_update",
        "answers_updated",
        "new_question_with_default",
        "true_conflict_markers",
        "conflict_command_completed",
        "required_question_without_default_fails",
        "nested_answers_updated",
    ]
    failures = [name for name in expected_true if results.get(name) is not True]
    if results.get("nested_answers_count") != 2:
        failures.append("nested_answers_count")
    results["failures"] = failures
    out = ROOT / "docs" / "results" / "copier-matrix.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit(f"Copier matrix failures: {failures}")


if __name__ == "__main__":
    main()
