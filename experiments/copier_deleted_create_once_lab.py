#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal

OwnershipMode = Literal["skip_if_exists", "exclude_on_update"]


def run(
    *args: str,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        result.check_returncode()
    return result


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git(repository: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run("git", *args, cwd=repository)


def commit(repository: Path, message: str) -> str:
    git(repository, "add", "-A")
    git(repository, "commit", "-m", message)
    return git(repository, "rev-parse", "HEAD").stdout.strip()


def copier_config(mode: OwnershipMode) -> str:
    ownership = {
        "skip_if_exists": """_skip_if_exists:
  - README.md
""",
        "exclude_on_update": """_exclude:
  - "{% if _copier_operation == 'update' -%}README.md{% endif %}"
""",
    }[mode]
    return f"""_min_copier_version: \"9.16.0\"
_subdirectory: template
_answers_file: .copier-answers.yml
_templates_suffix: \"\"
{ownership}project_name:
  type: str
  default: sample
"""


def create_template(root: Path, mode: OwnershipMode) -> tuple[Path, str, str]:
    template = root / f"template-{mode}"
    template.mkdir()
    git(template, "init", "-b", "main")
    git(template, "config", "user.name", "ternforge-lab")
    git(template, "config", "user.email", "ternforge-lab@example.invalid")

    write(template / "copier.yml", copier_config(mode))
    write(
        template / "template" / "{{ _copier_conf.answers_file }}",
        "{{ _copier_answers|to_nice_yaml|trim }}\n",
    )
    write(template / "template" / "README.md", "create-once v1\n")
    write(template / "template" / "managed.txt", "managed v1\n")
    v1_commit = commit(template, "template v1")
    git(template, "tag", "v0.1.0")

    write(template / "template" / "README.md", "create-once v2\n")
    write(template / "template" / "managed.txt", "managed v2\n")
    v2_commit = commit(template, "template v2")
    git(template, "tag", "v0.2.0")
    return template, v1_commit, v2_commit


def create_consumer(root: Path, mode: OwnershipMode, template: Path) -> tuple[Path, str]:
    consumer = root / f"consumer-{mode}"
    run(
        "copier",
        "copy",
        "--defaults",
        "--vcs-ref",
        "v0.1.0",
        str(template),
        str(consumer),
    )
    git(consumer, "init", "-b", "main")
    git(consumer, "config", "user.name", "ternforge-lab")
    git(consumer, "config", "user.email", "ternforge-lab@example.invalid")
    commit(consumer, "initial generated state")

    (consumer / "README.md").unlink()
    deletion_commit = commit(consumer, "delete create-once README")
    return consumer, deletion_commit


def run_scenario(root: Path, mode: OwnershipMode) -> dict[str, Any]:
    template, template_v1, template_v2 = create_template(root, mode)
    consumer, deletion_commit = create_consumer(root, mode, template)

    update = run(
        "copier",
        "update",
        "--skip-answered",
        "--defaults",
        "--answers-file",
        ".copier-answers.yml",
        "--vcs-ref",
        "v0.2.0",
        cwd=consumer,
        check=False,
    )

    readme = consumer / "README.md"
    managed = consumer / "managed.txt"
    answers = consumer / ".copier-answers.yml"
    files = [path for path in consumer.rglob("*") if path.is_file() and ".git" not in path.parts]

    return {
        "mode": mode,
        "template": {
            "v0.1.0_commit": template_v1,
            "v0.2.0_commit": template_v2,
        },
        "consumer": {
            "deletion_commit": deletion_commit,
            "diff_name_status_after_update": git(
                consumer, "diff", "--name-status"
            ).stdout.splitlines(),
            "readme_exists_after_update": readme.exists(),
            "readme_content_after_update": (
                readme.read_text(encoding="utf-8") if readme.exists() else None
            ),
            "managed_content_after_update": managed.read_text(encoding="utf-8"),
        },
        "update": {
            "returncode": update.returncode,
            "stdout": update.stdout,
            "stderr": update.stderr,
        },
        "checks": {
            "update_completed": update.returncode == 0,
            "managed_path_updated": managed.read_text(encoding="utf-8") == "managed v2\n",
            "answers_recorded_new_template_version": "v0.2.0"
            in answers.read_text(encoding="utf-8"),
            "no_reject_files": not any(consumer.rglob("*.rej")),
            "no_conflict_markers": not any(
                marker in path.read_text(encoding="utf-8", errors="ignore")
                for path in files
                for marker in ("<<<<<<<", "=======", ">>>>>>>")
            ),
        },
    }


def perform_experiment() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="copier-create-once-") as temporary:
        root = Path(temporary)
        skip = run_scenario(root, "skip_if_exists")
        exclude = run_scenario(root, "exclude_on_update")

        assertions = {
            "skip_if_exists_restored_deleted_path": skip["consumer"][
                "readme_exists_after_update"
            ]
            is True,
            "exclude_on_update_preserved_deletion": exclude["consumer"][
                "readme_exists_after_update"
            ]
            is False,
            "both_updates_completed": skip["checks"]["update_completed"]
            and exclude["checks"]["update_completed"],
            "both_managed_paths_updated": skip["checks"]["managed_path_updated"]
            and exclude["checks"]["managed_path_updated"],
            "both_answers_advanced": skip["checks"][
                "answers_recorded_new_template_version"
            ]
            and exclude["checks"]["answers_recorded_new_template_version"],
            "both_updates_clean": skip["checks"]["no_reject_files"]
            and skip["checks"]["no_conflict_markers"]
            and exclude["checks"]["no_reject_files"]
            and exclude["checks"]["no_conflict_markers"],
        }

        return {
            "question": (
                "Which native Copier 9.16.0 rule expresses create-once ownership "
                "while preserving an intentional deletion during later updates?"
            ),
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "copier": run("copier", "--version").stdout.strip(),
                "git": run("git", "--version").stdout.strip(),
            },
            "scenarios": {
                "skip_if_exists": skip,
                "exclude_on_update": exclude,
            },
            "assertions": assertions,
            "outcome": "passed" if all(assertions.values()) else "failed",
            "conclusion": (
                "_skip_if_exists protects an existing destination but recreates it after "
                "deletion. A Jinja-templated _exclude rule keyed by _copier_operation "
                "prevents the path from rendering on update and preserves deletion."
            ),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = perform_experiment()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(0 if result["outcome"] == "passed" else 1)


if __name__ == "__main__":
    main()
