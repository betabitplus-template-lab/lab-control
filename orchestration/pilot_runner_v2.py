#!/usr/bin/env python3
from __future__ import annotations

import os
import textwrap
import tempfile
from pathlib import Path

runner_path = Path(__file__).with_name("pilot_runner.py")
source = runner_path.read_text(encoding="utf-8")
source = source.rsplit("pilot.prepare()", 1)[0]
source = source.replace(
    "component_source.relative_to(template).as_posix()",
    "component_source.relative_to(template.parent).as_posix()",
)
namespace: dict[str, object] = {
    "__name__": "pilot_runner_patched",
    "__file__": str(runner_path),
}
exec(compile(source, str(runner_path), "exec"), namespace)
pilot = namespace["pilot"]


def composition_fixture(components: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "fixture"
        template = root / "template"
        payload = root / "payload"
        payload.mkdir(parents=True)
        (payload / "plain.txt").write_text("plain\n", encoding="utf-8")
        (payload / "templated.txt").write_text(
            "hello [[[ project_name ]]]\n", encoding="utf-8"
        )
        (payload / "empty.txt").write_bytes(b"")
        (payload / "binary.bin").write_bytes(bytes(range(256)))
        pilot.write(payload / "run.sh", "#!/usr/bin/env bash\necho ok\n", 0o755)
        (payload / "directory").mkdir()
        (payload / "directory" / "nested.txt").write_text(
            "nested\n", encoding="utf-8"
        )
        template.mkdir(parents=True)
        (template / "_components").symlink_to(payload, target_is_directory=True)
        for name in ["plain.txt", "templated.txt", "empty.txt", "binary.bin", "run.sh"]:
            (template / name).symlink_to(Path("_components") / name)
        forbidden_directory = template / "whole-directory"
        forbidden_directory.symlink_to(
            Path("_components") / "directory", target_is_directory=True
        )
        pilot.write(
            template / "wrapper.txt",
            '[[% include "template/_components/templated.txt" %]]',
        )
        pilot.write(
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
        pilot.run("git", "init", "-b", "main", cwd=root)
        pilot.run("git", "add", "-A", cwd=root)
        pilot.run(
            "git",
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-m",
            "fixture with forbidden directory symlink",
            cwd=root,
        )
        forbidden_out = Path(td) / "forbidden-out"
        forbidden = pilot.run(
            "copier",
            "copy",
            "--defaults",
            "--vcs-ref",
            "HEAD",
            str(root),
            str(forbidden_out),
            capture=True,
            check=False,
        )
        assert forbidden.returncode != 0
        assert "ForbiddenPathError" in forbidden.stderr or "is forbidden" in forbidden.stderr

        forbidden_directory.unlink()
        pilot.run("git", "add", "-A", cwd=root)
        pilot.run(
            "git",
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-m",
            "remove forbidden directory symlink",
            cwd=root,
        )
        out = Path(td) / "out"
        pilot.run(
            "copier",
            "copy",
            "--defaults",
            "--vcs-ref",
            "HEAD",
            str(root),
            str(out),
        )
        assert not (out / "_components").exists()
        assert (out / "plain.txt").read_text(encoding="utf-8") == "plain\n"
        assert (out / "templated.txt").read_text(encoding="utf-8") == "hello fixture\n"
        assert (out / "wrapper.txt").read_text(encoding="utf-8") == "hello fixture\n"
        assert (out / "empty.txt").read_bytes() == b""
        assert (out / "binary.bin").read_bytes() == bytes(range(256))
        if os.name != "nt":
            assert pilot.executable(out / "run.sh")
        return {
            "text_symlink": True,
            "jinja_symlink": True,
            "jinja_include": True,
            "executable": True,
            "binary": True,
            "empty": True,
            "directory_symlink": False,
            "directory_symlink_result": "Copier ForbiddenPathError",
            "excluded_loader_source": True,
            "loader_root": "repository-root",
        }


pilot.composition_fixture = composition_fixture
pilot.prepare()
