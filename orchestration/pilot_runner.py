#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
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
    pilot.safe_rmtree(repo / ".git" / "modules" / "template" / "_components")
    for child in repo.iterdir():
        if child.name in {".git", ".github"}:
            continue
        pilot.safe_rmtree(child)
    pilot.git(repo, "add", "-A")
    if pilot.git_output(repo, "status", "--porcelain"):
        pilot.git(repo, "commit", "-m", "chore: reset isolated lab tree")


def is_text(data: bytes) -> bool:
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def wire_components(
    template: Path,
    components: Path,
    names: list[str],
) -> dict[str, dict[str, object]]:
    ownership: dict[str, tuple[str, Path]] = {}
    for component in names:
        payload = components / component / "template"
        if not payload.is_dir():
            raise pilot.PilotError(f"missing component payload: {component}")
        for source_path in pilot.component_files(payload):
            rel = source_path.relative_to(payload).as_posix()
            if rel in ownership:
                raise pilot.PilotError(
                    f"component collision for {rel}: {ownership[rel][0]} and {component}"
                )
            ownership[rel] = (component, source_path)

    wiring: dict[str, dict[str, object]] = {}
    for source_rel, (component, component_path) in sorted(ownership.items()):
        output_rel = source_rel
        target = template / output_rel
        if not target.exists() and not target.is_symlink():
            if "_copier_conf.answers_file" in source_rel:
                alternatives = [
                    template / "_copier_answers.yml",
                    template / "_copier_answers.platform.yml",
                ]
                existing = next((path for path in alternatives if path.exists()), None)
                if existing is None:
                    raise pilot.PilotError(
                        f"missing build target for dynamic answers file: {source_rel}"
                    )
                target = existing
                output_rel = target.relative_to(template).as_posix()
            else:
                raise pilot.PilotError(
                    f"component output absent from frozen build: {component}:{source_rel}"
                )

        data = component_path.read_bytes()
        if target.read_bytes() != data:
            raise pilot.PilotError(
                f"content mismatch before wiring: {component}:{output_rel}"
            )
        source_executable = pilot.executable(component_path)
        if pilot.executable(target) != source_executable:
            raise pilot.PilotError(
                f"mode mismatch before wiring: {component}:{output_rel}"
            )

        target.unlink()
        component_source = (
            template / "_components" / component / "template" / source_rel
        )
        use_wrapper = (
            source_executable
            or output_rel == ".gitignore"
            or component_path.is_symlink()
        )
        if use_wrapper and is_text(data):
            include_path = component_source.relative_to(template).as_posix()
            target.write_text(f'[[% include "{include_path}" %]]', encoding="utf-8")
            target.chmod(0o755 if source_executable else 0o644)
            wiring_type = "jinja-wrapper"
        elif use_wrapper:
            target.write_bytes(data)
            target.chmod(0o755 if source_executable else 0o644)
            wiring_type = "binary-copy-fallback"
        else:
            target.symlink_to(os.path.relpath(component_source, start=target.parent))
            wiring_type = "file-symlink"

        wiring[output_rel] = {
            "component": component,
            "source": component_source.relative_to(template).as_posix(),
            "executable": source_executable,
            "sha256": hashlib.sha256(data).hexdigest(),
            "type": wiring_type,
        }
    return wiring


pilot.TEMPLATE_ACCEPTANCE = r'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
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
        kind = info["type"]
        if kind == "file-symlink":
            assert path.is_symlink(), f"not a symlink: {rel}"
            resolved = path.resolve(strict=True)
            assert "_components" in resolved.parts, f"outside submodule: {rel}"
            source = resolved
        else:
            assert path.is_file() and not path.is_symlink(), rel
            source = ROOT / "template" / info["source"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == info["sha256"], rel
        assert executable(source) == bool(info["executable"]), rel

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "generated"
        run("copier", "copy", "--defaults", "--vcs-ref", "HEAD", str(ROOT), str(out))
        assert (out / ".copier-answers.yml").is_file()
        assert not (out / "_components").exists()
        for file in out.rglob("*"):
            if not file.is_file():
                continue
            try:
                text = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            assert not ("<<<<<<< " in text and "\n=======\n" in text and "\n>>>>>>> " in text), file
        executable_outputs = [rel for rel, info in wiring.items() if info["executable"]]
        if executable_outputs and os.name != "nt":
            assert executable(out / executable_outputs[0]), executable_outputs[0]
        print(json.dumps({
            "repository": ROOT.name,
            "wiring_files": len(wiring),
            "rendered_files": sum(1 for path in out.rglob("*") if path.is_file()),
            "platform": os.name,
        }, sort_keys=True))


if __name__ == "__main__":
    main()
'''

pilot.run = safe_run
pilot.clean_repo = clean_repo
pilot.wire_components = wire_components
pilot.prepare()
