#!/usr/bin/env python3
from __future__ import annotations

import filecmp
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

ORG = "betabitplus-template-lab"
SOURCE_REPO = "betabitplus/py-lib-starter"
SOURCE_SHA = "d59582375855cff69fb165e467dc5847bc75ca99"
COPIER_VERSION = "9.16.0"
EXPECTED_REPOS = {
    "components",
    "python-lib",
    "python-internal-package",
    "python-starter-platform",
    "sandbox-python-lib",
    "sandbox-python-platform",
    "sandbox-workspace",
    "lab-control",
}

TEMPLATE_PROFILES = {
    "python-lib": "python-lib-standard",
    "python-internal-package": "python-internal-package",
    "python-starter-platform": "python-starter-platform",
}

RENOVATE_TEMPLATE = """{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "enabledManagers": ["git-submodules"],
  "git-submodules": { "enabled": true },
  "automerge": false,
  "dependencyDashboard": true,
  "branchPrefix": "renovate-lab/",
  "packageRules": [
    {
      "matchManagers": ["git-submodules"],
      "matchDepNames": ["template/_components"],
      "groupName": "template components",
      "addLabels": ["template-components", "lab"]
    }
  ]
}
"""

RENOVATE_DOWNSTREAM = """{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "enabledManagers": ["copier"],
  "automerge": false,
  "dependencyDashboard": true,
  "branchPrefix": "renovate-lab/",
  "packageRules": [
    {
      "matchManagers": ["copier"],
      "addLabels": ["template-update", "lab"]
    }
  ]
}
"""

TEMPLATE_ACCEPTANCE = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd or ROOT, text=True, capture_output=True, check=True)


def executable(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


def main() -> None:
    wiring = json.loads((ROOT / "WIRING.json").read_text(encoding="utf-8"))
    assert wiring, "empty wiring"
    assert (ROOT / "template" / "_components").exists()
    for rel, info in wiring.items():
        path = ROOT / "template" / rel
        assert path.is_symlink(), f"not a symlink: {rel}"
        resolved = path.resolve(strict=True)
        assert "_components" in resolved.parts, f"outside submodule: {rel}"
        assert executable(resolved) == bool(info["executable"]), rel

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "generated"
        run("copier", "copy", "--defaults", "--vcs-ref", "HEAD", str(ROOT), str(out))
        assert (out / ".copier-answers.yml").is_file()
        assert not (out / "_components").exists()
        assert not (out / "template" / "_components").exists()
        for file in out.rglob("*"):
            if not file.is_file():
                continue
            try:
                text = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            assert not ("<<<<<<< " in text and "\n=======\n" in text and "\n>>>>>>> " in text), file

        # A component-owned executable must remain executable after dereferencing.
        executable_outputs = [rel for rel, info in wiring.items() if info["executable"]]
        if executable_outputs and os.name != "nt":
            assert executable(out / executable_outputs[0]), executable_outputs[0]

        result = {
            "repository": ROOT.name,
            "wiring_files": len(wiring),
            "rendered_files": sum(1 for p in out.rglob("*") if p.is_file()),
            "platform": os.name,
        }
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
'''

SANDBOX_CI = r'''#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    answers = list(ROOT.rglob(".copier-answers.yml"))
    assert answers, "no Copier relationship found"
    for answer in answers:
        text = answer.read_text(encoding="utf-8")
        assert "_src_path:" in text
        assert "_commit:" in text
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert not ("<<<<<<< " in text and "\n=======\n" in text and "\n>>>>>>> " in text), path
    print(f"answers={len(answers)}")


if __name__ == "__main__":
    main()
'''


class PilotError(RuntimeError):
    pass


def run(
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = [str(a) for a in args]
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=capture,
        check=check,
    )


def output(*args: str, cwd: Path | None = None) -> str:
    return run(*args, cwd=cwd, capture=True).stdout.strip()


def git(repo: Path, *args: str, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", *args, cwd=repo, capture=capture, check=check)


def git_output(repo: Path, *args: str) -> str:
    return output("git", *args, cwd=repo)


def write(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def executable(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


def safe_rmtree(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink() or path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)


def configure_git(token: str) -> None:
    run("git", "config", "--global", "user.name", "Template Lab Orchestrator")
    run("git", "config", "--global", "user.email", "8123085+betabitplus@users.noreply.github.com")
    run(
        "git",
        "config",
        "--global",
        f"url.https://x-access-token:{token}@github.com/.insteadOf",
        "https://github.com/",
    )


def clone(repo: str, root: Path, *, source: bool = False) -> Path:
    destination = root / repo.split("/")[-1]
    url = f"https://github.com/{repo}.git"
    run("git", "clone", "--no-tags" if source else "--recurse-submodules", url, str(destination))
    if source:
        git(destination, "fetch", "origin", SOURCE_SHA)
        git(destination, "checkout", "--detach", SOURCE_SHA)
        actual = git_output(destination, "rev-parse", "HEAD")
        if actual != SOURCE_SHA:
            raise PilotError(f"source SHA mismatch: {actual}")
        if git_output(destination, "status", "--porcelain"):
            raise PilotError("source clone is dirty")
    return destination


def clean_repo(repo: Path) -> None:
    # Preserve Git metadata and pre-installed workflows. Workflow changes are made
    # only through the ChatGPT connector because the lab App intentionally has no
    # Workflows permission.
    git(repo, "submodule", "deinit", "-f", "--all", check=False)
    for child in repo.iterdir():
        if child.name in {".git", ".github"}:
            continue
        safe_rmtree(child)


def transform_copier(source: Path, profile: str, destination: Path) -> None:
    lines = source.read_text(encoding="utf-8").splitlines()
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("_subdirectory:"):
            result.append('_subdirectory: "template"')
            i += 1
            continue
        if line.startswith("_answers_file:"):
            result.append('_answers_file: ".copier-answers.yml"')
            i += 1
            continue
        if line == "template_profile:":
            while i < len(lines) and lines[i] != "project_name:":
                i += 1
            result.extend(
                [
                    "template_profile:",
                    "  type: str",
                    f"  default: {profile}",
                    "  when: false",
                    "",
                ]
            )
            continue
        result.append(line)
        i += 1
    insert_at = result.index("_envops:")
    result[insert_at:insert_at] = [
        "_exclude:",
        "  - _components",
        "  - _components/**",
        "",
    ]
    write(destination, "\n".join(result) + "\n")


def resolve_components(source: Path, profile: str) -> list[str]:
    manifests = source / "template-manifests"
    data = yaml.safe_load((manifests / profile / "manifest.yml").read_text(encoding="utf-8"))
    if "extends" not in data:
        return list(data.get("components", []))
    base = resolve_components(source, str(data["extends"]))
    excluded = set(data.get("exclude_components", []))
    return [component for component in base if component not in excluded]


def component_files(component_root: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(component_root, followlinks=False):
        root_path = Path(root)
        # Directory symlinks are handled as a single entry and not traversed.
        for name in list(dirs):
            path = root_path / name
            if path.is_symlink():
                yield path
                dirs.remove(name)
        for name in files:
            yield root_path / name


def wire_components(template: Path, components: Path, names: list[str]) -> dict[str, dict[str, object]]:
    ownership: dict[str, tuple[str, Path]] = {}
    for component in names:
        payload = components / component / "template"
        if not payload.is_dir():
            raise PilotError(f"missing component payload: {component}")
        for source_path in component_files(payload):
            rel = source_path.relative_to(payload).as_posix()
            if rel in ownership:
                raise PilotError(f"component collision for {rel}: {ownership[rel][0]} and {component}")
            ownership[rel] = (component, source_path)

    wiring: dict[str, dict[str, object]] = {}
    for rel, (component, component_path) in sorted(ownership.items()):
        target = template / rel
        if not target.exists() and not target.is_symlink():
            # Copier answer payloads can use a Jinja-derived output filename while
            # the frozen build stores the profile-specific resolved filename.
            if "_copier_conf.answers_file" in rel:
                alternatives = [template / "_copier_answers.yml", template / "_copier_answers.platform.yml"]
                existing = next((p for p in alternatives if p.exists()), None)
                if existing is None:
                    raise PilotError(f"missing build target for dynamic answers file: {rel}")
                target = existing
                rel = target.relative_to(template).as_posix()
            else:
                raise PilotError(f"component output absent from frozen build: {component}:{rel}")

        if component_path.is_dir() and component_path.is_symlink():
            # Main profiles currently do not contain directory symlink payloads.
            raise PilotError(f"unexpected directory symlink in production component: {component}:{rel}")

        if target.read_bytes() != component_path.read_bytes():
            raise PilotError(f"content mismatch before wiring: {component}:{rel}")
        if executable(target) != executable(component_path):
            raise PilotError(f"mode mismatch before wiring: {component}:{rel}")

        target.unlink()
        link_target = template / "_components" / component / "template" / component_path.relative_to(
            components / component / "template"
        )
        target.symlink_to(os.path.relpath(link_target, start=target.parent))
        wiring[rel] = {
            "component": component,
            "source": link_target.relative_to(template).as_posix(),
            "executable": executable(component_path),
            "sha256": hashlib.sha256(component_path.read_bytes()).hexdigest(),
        }
    return wiring


def remove_legacy_sync(template: Path) -> list[str]:
    removed: list[str] = []
    workflows = template / ".github" / "workflows"
    if workflows.is_dir():
        for path in workflows.glob("*sync*.y*ml"):
            removed.append(path.relative_to(template).as_posix())
            path.unlink()
    return removed


def add_static_overlays(template: Path, profile: str) -> list[str]:
    overlays: list[str] = []
    if profile in {"python-lib-standard", "python-starter-platform"}:
        path = template / "renovate.json5"
        if path.exists() or path.is_symlink():
            path.unlink()
        write(path, RENOVATE_DOWNSTREAM)
        overlays.append("renovate.json5")
    return overlays


def commit_push(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    if not git_output(repo, "status", "--porcelain"):
        return git_output(repo, "rev-parse", "HEAD")
    git(repo, "commit", "-m", message)
    git(repo, "push", "origin", "main")
    return git_output(repo, "rev-parse", "HEAD")


def tag_if_missing(repo: Path, tag: str, message: str) -> str:
    git(repo, "fetch", "origin", "--tags")
    existing = run("git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}", cwd=repo, capture=True, check=False)
    if existing.returncode == 0:
        return existing.stdout.strip()
    git(repo, "tag", "-a", tag, "-m", message)
    git(repo, "push", "origin", tag)
    return git_output(repo, "rev-parse", tag)


def build_template(
    repo: Path,
    source: Path,
    components: Path,
    profile: str,
    components_sha: str,
) -> dict[str, object]:
    workflows = repo / ".github"
    clean_repo(repo)
    if workflows.exists():
        workflows.mkdir(parents=True, exist_ok=True)

    template = repo / "template"
    shutil.copytree(source / "template-builds" / profile, template, symlinks=True)
    git(repo, "submodule", "add", "-b", "main", f"https://github.com/{ORG}/components.git", "template/_components")
    git(template / "_components", "checkout", components_sha)

    transform_copier(source / "copier.yml", profile, repo / "copier.yml")
    component_names = resolve_components(source, profile)
    wiring = wire_components(template, components, component_names)
    removed = remove_legacy_sync(template)
    overlays = add_static_overlays(template, profile)

    write(repo / "renovate.json5", RENOVATE_TEMPLATE)
    write(
        repo / "SOURCE.yml",
        yaml.safe_dump(
            {
                "source_repository": SOURCE_REPO,
                "source_ref": SOURCE_SHA,
                "source_path": f"template-builds/{profile}",
                "manifest_path": f"template-manifests/{profile}/manifest.yml",
                "components_repository": f"{ORG}/components",
                "components_ref": components_sha,
            },
            sort_keys=False,
        ),
    )
    write(repo / "WIRING.json", json.dumps(wiring, indent=2, sort_keys=True) + "\n")
    write(repo / "tests" / "template_acceptance.py", TEMPLATE_ACCEPTANCE, 0o755)
    write(
        repo / "README.md",
        textwrap.dedent(
            f"""\
            # {repo.name}

            Isolated Copier template for `{profile}`.

            - frozen source: `{SOURCE_REPO}@{SOURCE_SHA}`
            - components: private Git submodule pinned by exact SHA
            - component-owned files: committed static symlink wiring
            - no production repository is a write target
            """
        ),
    )
    return {
        "profile": profile,
        "components": component_names,
        "wiring_files": len(wiring),
        "removed_legacy_paths": removed,
        "overlays": overlays,
    }


def render(template_repo: Path, destination: Path, data: dict[str, str] | None = None) -> None:
    args = ["copier", "copy", "--defaults", "--vcs-ref", "HEAD"]
    for key, value in (data or {}).items():
        args.extend(["--data", f"{key}={value}"])
    args.extend([str(template_repo), str(destination)])
    run(*args)


def render_baseline(source: Path, profile: str, destination: Path, data: dict[str, str] | None = None) -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "baseline-template"
        root.mkdir()
        shutil.copytree(source / "template-builds" / profile, root / "template", symlinks=True)
        transform_copier(source / "copier.yml", profile, root / "copier.yml")
        run("git", "init", "-b", "main", cwd=root)
        run("git", "add", "-A", cwd=root)
        run("git", "-c", "user.name=baseline", "-c", "user.email=baseline@example.invalid", "commit", "-m", "baseline", cwd=root)
        render(root, destination, data)


def file_inventory(root: Path, ignored: set[str]) -> dict[str, tuple[str, bool]]:
    result: dict[str, tuple[str, bool]] = {}
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(root).as_posix()
        if rel in ignored or any(rel.startswith(prefix.rstrip("*") ) for prefix in []):
            continue
        data = path.read_bytes()
        result[rel] = (hashlib.sha256(data).hexdigest(), executable(path))
    return result


def parity_test(source: Path, repo: Path, profile: str, data: dict[str, str] | None = None) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "base"
        candidate = Path(td) / "candidate"
        render_baseline(source, profile, base, data)
        render(repo, candidate, data)
        ignored = {
            ".copier-answers.yml",
            "_copier_answers.yml",
            "_copier_answers.platform.yml",
            "renovate.json5",
        }
        for root in (base, candidate):
            workflows = root / ".github" / "workflows"
            if workflows.exists():
                for path in workflows.glob("*sync*.y*ml"):
                    ignored.add(path.relative_to(root).as_posix())
        base_inventory = file_inventory(base, ignored)
        candidate_inventory = file_inventory(candidate, ignored)
        if base_inventory != candidate_inventory:
            missing = sorted(set(base_inventory) - set(candidate_inventory))
            extra = sorted(set(candidate_inventory) - set(base_inventory))
            changed = sorted(
                path
                for path in set(base_inventory) & set(candidate_inventory)
                if base_inventory[path] != candidate_inventory[path]
            )
            raise PilotError(
                f"parity failed for {repo.name}/{data or 'defaults'}: missing={missing[:20]} extra={extra[:20]} changed={changed[:20]}"
            )
        return {"files": len(candidate_inventory), "ignored": sorted(ignored)}


def composition_fixture(components: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "fixture"
        template = root / "template"
        payload = root / "payload"
        payload.mkdir(parents=True)
        (payload / "plain.txt").write_text("plain\n", encoding="utf-8")
        (payload / "templated.txt").write_text("hello [[[ project_name ]]]\n", encoding="utf-8")
        (payload / "empty.txt").write_bytes(b"")
        (payload / "binary.bin").write_bytes(bytes(range(256)))
        write(payload / "run.sh", "#!/usr/bin/env bash\necho ok\n", 0o755)
        (payload / "directory").mkdir()
        (payload / "directory" / "nested.txt").write_text("nested\n", encoding="utf-8")
        template.mkdir(parents=True)
        (template / "_components").symlink_to(payload, target_is_directory=True)
        for name in ["plain.txt", "templated.txt", "empty.txt", "binary.bin", "run.sh"]:
            (template / name).symlink_to(Path("_components") / name)
        (template / "whole-directory").symlink_to(Path("_components") / "directory", target_is_directory=True)
        write(template / "wrapper.txt", '[[% include "_components/templated.txt" %]]')
        write(
            root / "copier.yml",
            textwrap.dedent(
                """\
                _min_copier_version: "9.16.0"
                _subdirectory: template
                _templates_suffix: ""
                _exclude:
                  - _components
                  - _components/**
                _envops:
                  variable_start_string: "[[["
                  variable_end_string: "]]]"
                  block_start_string: "[[%"
                  block_end_string: "%]]"
                project_name:
                  type: str
                  default: fixture
                """
            ),
        )
        run("git", "init", "-b", "main", cwd=root)
        run("git", "add", "-A", cwd=root)
        run("git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture", cwd=root)
        out = Path(td) / "out"
        run("copier", "copy", "--defaults", "--vcs-ref", "HEAD", str(root), str(out))
        assert not (out / "_components").exists()
        assert (out / "plain.txt").read_text(encoding="utf-8") == "plain\n"
        assert (out / "templated.txt").read_text(encoding="utf-8") == "hello fixture\n"
        assert (out / "wrapper.txt").read_text(encoding="utf-8") == "hello fixture\n"
        assert (out / "empty.txt").read_bytes() == b""
        assert (out / "binary.bin").read_bytes() == bytes(range(256))
        assert (out / "whole-directory" / "nested.txt").read_text(encoding="utf-8") == "nested\n"
        if os.name != "nt":
            assert executable(out / "run.sh")
        return {
            "text_symlink": True,
            "jinja_symlink": True,
            "jinja_include": True,
            "executable": True,
            "binary": True,
            "empty": True,
            "directory_symlink": True,
            "excluded_loader_source": True,
        }


def reset_generated_repo(repo: Path) -> None:
    for child in repo.iterdir():
        if child.name in {".git", ".github"}:
            continue
        safe_rmtree(child)


def copier_remote(repo_name: str) -> str:
    return f"https://github.com/{ORG}/{repo_name}.git"


def generate_sandbox(repo: Path, template_name: str, tag: str, data: dict[str, str]) -> None:
    reset_generated_repo(repo)
    args = ["copier", "copy", "--defaults", "--vcs-ref", tag]
    for key, value in data.items():
        args.extend(["--data", f"{key}={value}"])
    args.extend([copier_remote(template_name), str(repo)])
    run(*args)
    write(repo / "renovate.json5", RENOVATE_DOWNSTREAM)
    write(repo / "tests" / "lab_ci.py", SANDBOX_CI, 0o755)


def add_user_changes(repo: Path, package_name: str | None = None) -> None:
    write(repo / "LAB_USER_OWNED.txt", "This file belongs to the downstream user and must survive Copier updates.\n")
    if package_name:
        path = repo / "src" / package_name / "domain.py"
        write(path, '"""User-owned downstream module."""\n\nVALUE = "preserve-me"\n')
    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        marker = "# downstream-user-note: preserve across template updates\n"
        if marker not in text:
            pyproject.write_text(marker + text, encoding="utf-8")


def prepare_workspace(repo: Path) -> None:
    reset_generated_repo(repo)
    for name, package in [("runtime", "workspace_runtime"), ("tooling", "workspace_tooling")]:
        destination = repo / "packages" / name
        run(
            "copier",
            "copy",
            "--defaults",
            "--vcs-ref",
            "v0.1.0",
            "--data",
            f"project_name=workspace-{name}",
            "--data",
            f"package_name={package}",
            copier_remote("python-internal-package"),
            str(destination),
        )
        write(destination / "USER_OWNED.txt", f"user file for {name}\n")
    write(repo / "renovate.json5", RENOVATE_DOWNSTREAM)
    write(repo / "tests" / "lab_ci.py", SANDBOX_CI, 0o755)
    write(repo / "README.md", "# sandbox-workspace\n\nTwo independent nested Copier relationships.\n")


def validate_answers(repo: Path, expected: int) -> None:
    answers = list(repo.rglob(".copier-answers.yml"))
    if len(answers) != expected:
        raise PilotError(f"{repo.name}: expected {expected} answers files, got {len(answers)}")
    for answer in answers:
        text = answer.read_text(encoding="utf-8")
        if f"{ORG}/" not in text:
            raise PilotError(f"{answer}: non-lab source path")


def prepare() -> None:
    token = os.environ.get("LAB_TOKEN")
    if not token:
        raise PilotError("LAB_TOKEN is required")
    request_path = Path(os.environ.get("GITHUB_WORKSPACE", ".")) / "orchestration" / "request.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if request.get("organization") != ORG or request.get("action") != "prepare":
        raise PilotError(f"unsafe request: {request}")
    expected_sha = request.get("components_sha")
    if not isinstance(expected_sha, str) or len(expected_sha) != 40:
        raise PilotError("request must pin the initial components SHA")

    configure_git(token)
    with tempfile.TemporaryDirectory(prefix="template-lab-") as td:
        root = Path(td)
        source = clone(SOURCE_REPO, root, source=True)
        repos = {name: clone(f"{ORG}/{name}", root) for name in sorted(EXPECTED_REPOS - {"lab-control"})}
        components = repos["components"]
        actual_components_sha = git_output(components, "rev-parse", "HEAD")
        if actual_components_sha != expected_sha:
            raise PilotError(f"components SHA changed before prepare: {actual_components_sha} != {expected_sha}")

        report: dict[str, object] = {
            "source": {"repository": SOURCE_REPO, "sha": SOURCE_SHA},
            "components_initial_sha": actual_components_sha,
            "templates": {},
            "sandboxes": {},
            "composition": {},
            "safety": {
                "allowed_write_owner": ORG,
                "source_detached_clean": True,
                "production_mutations": 0,
            },
        }

        for repo_name, profile in TEMPLATE_PROFILES.items():
            repo = repos[repo_name]
            info = build_template(repo, source, components, profile, actual_components_sha)
            commit = commit_push(repo, f"feat: implement isolated {profile} Copier template")
            info["commit"] = commit
            info["parity_defaults"] = parity_test(source, repo, profile)
            info["parity_custom"] = parity_test(
                source,
                repo,
                profile,
                {
                    "project_name": f"custom-{repo_name}",
                    "package_name": f"custom_{repo_name.replace('-', '_')}",
                    "author_name": "Template Lab",
                    "github_owner": ORG,
                },
            )
            if repo_name != "python-lib":
                info["tag_v0.1.0"] = tag_if_missing(repo, "v0.1.0", f"{repo_name} lab v0.1.0")
            else:
                info["tag_v0.1.0"] = git_output(repo, "rev-parse", "v0.1.0")
            report["templates"][repo_name] = info

        report["composition"] = composition_fixture(components)

        sandbox_lib = repos["sandbox-python-lib"]
        add_user_changes(sandbox_lib, "sandbox_python_lib")
        report["sandboxes"]["sandbox-python-lib"] = {
            "commit": commit_push(sandbox_lib, "test: add downstream user-owned changes"),
            "answers": 1,
            "template_version": "v0.1.0",
        }
        validate_answers(sandbox_lib, 1)

        sandbox_platform = repos["sandbox-python-platform"]
        generate_sandbox(
            sandbox_platform,
            "python-starter-platform",
            "v0.1.0",
            {"project_name": "sandbox-python-platform", "package_name": "sandbox_python_platform"},
        )
        add_user_changes(sandbox_platform, "sandbox_python_platform")
        report["sandboxes"]["sandbox-python-platform"] = {
            "commit": commit_push(sandbox_platform, "feat: generate platform sandbox from v0.1.0"),
            "answers": 1,
            "template_version": "v0.1.0",
        }
        validate_answers(sandbox_platform, 1)

        workspace = repos["sandbox-workspace"]
        prepare_workspace(workspace)
        report["sandboxes"]["sandbox-workspace"] = {
            "commit": commit_push(workspace, "feat: generate two nested Copier relationships"),
            "answers": 2,
            "template_version": "v0.1.0",
        }
        validate_answers(workspace, 2)

        report_path = Path(os.environ.get("GITHUB_WORKSPACE", ".")) / "docs" / "results" / "prepare.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown = [
            "# Pilot preparation result",
            "",
            f"- source: `{SOURCE_REPO}@{SOURCE_SHA}`",
            f"- components C1: `{actual_components_sha}`",
            "- all writes restricted to `betabitplus-template-lab/*`",
            "- all three template profiles rendered and matched the frozen baseline",
            "- static component symlink wiring committed in all three templates",
            "- composition fixture passed text, executable, Jinja, binary, empty, directory and exclusion checks",
            "- platform sandbox and two-relationship workspace generated from private tags",
            "",
            "Machine-readable details: [`prepare.json`](prepare.json).",
            "",
        ]
        write(report_path.with_suffix(".md"), "\n".join(markdown))
        workspace_root = Path(os.environ.get("GITHUB_WORKSPACE", "."))
        git(workspace_root, "add", "docs/results/prepare.json", "docs/results/prepare.md")
        if git_output(workspace_root, "status", "--porcelain"):
            git(workspace_root, "commit", "-m", "docs: record pilot preparation results")
            git(workspace_root, "push", "origin", "main")


if __name__ == "__main__":
    try:
        prepare()
    except Exception as exc:
        print(f"PILOT FAILED: {exc}", file=sys.stderr)
        raise
