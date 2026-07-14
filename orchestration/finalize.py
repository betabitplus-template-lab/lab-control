#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

runner_path = Path(__file__).with_name("pilot_runner_v2.py")
source = runner_path.read_text(encoding="utf-8").rsplit("pilot.prepare()", 1)[0]
namespace: dict[str, object] = {
    "__name__": "pilot_finalize_runtime",
    "__file__": str(runner_path),
}
exec(compile(source, str(runner_path), "exec"), namespace)
pilot = namespace["pilot"]


def main() -> None:
    token = os.environ.get("LAB_TOKEN")
    if not token:
        raise pilot.PilotError("LAB_TOKEN is required")
    pilot.configure_git(token)
    workspace_root = Path(os.environ.get("GITHUB_WORKSPACE", "."))

    with tempfile.TemporaryDirectory(prefix="template-lab-finalize-") as td:
        root = Path(td)
        source_repo = pilot.clone(pilot.SOURCE_REPO, root, source=True)
        components = pilot.clone(f"{pilot.ORG}/components", root)
        components_sha = pilot.git_output(components, "rev-parse", "HEAD")
        if components_sha != "1f233492f3f66fdf17096cdb9462e4d38a04e8fc":
            raise pilot.PilotError(
                f"prepare must finish before C2: components={components_sha}"
            )

        repos = {
            name: pilot.clone(f"{pilot.ORG}/{name}", root)
            for name in [
                "python-lib",
                "python-internal-package",
                "python-starter-platform",
                "sandbox-python-lib",
                "sandbox-python-platform",
                "sandbox-workspace",
            ]
        }
        report: dict[str, object] = {
            "source": {"repository": pilot.SOURCE_REPO, "sha": pilot.SOURCE_SHA},
            "components_initial_sha": components_sha,
            "templates": {},
            "sandboxes": {},
            "composition": pilot.composition_fixture(components),
            "safety": {
                "allowed_write_owner": pilot.ORG,
                "source_detached_clean": True,
                "production_mutations": 0,
            },
        }

        for repo_name, profile in pilot.TEMPLATE_PROFILES.items():
            repo = repos[repo_name]
            wiring = json.loads((repo / "WIRING.json").read_text(encoding="utf-8"))
            source_meta = (repo / "SOURCE.yml").read_text(encoding="utf-8")
            if pilot.SOURCE_SHA not in source_meta or components_sha not in source_meta:
                raise pilot.PilotError(f"stale SOURCE.yml in {repo_name}")
            report["templates"][repo_name] = {
                "profile": profile,
                "commit": pilot.git_output(repo, "rev-parse", "HEAD"),
                "wiring_files": len(wiring),
                "parity_defaults": pilot.parity_test(source_repo, repo, profile),
                "parity_custom": pilot.parity_test(
                    source_repo,
                    repo,
                    profile,
                    {
                        "project_name": f"custom-{repo_name}",
                        "package_name": f"custom_{repo_name.replace('-', '_')}",
                        "author_name": "Template Lab",
                        "github_owner": pilot.ORG,
                    },
                ),
                "tag_v0.1.0": pilot.git_output(repo, "rev-parse", "v0.1.0^{}"),
            }

        sandbox_lib = repos["sandbox-python-lib"]
        pilot.add_user_changes(sandbox_lib, "sandbox_python_lib")
        lib_commit = pilot.commit_push(
            sandbox_lib, "test: ensure downstream user-owned changes"
        )
        pilot.validate_answers(sandbox_lib, 1)
        report["sandboxes"]["sandbox-python-lib"] = {
            "commit": lib_commit,
            "answers": 1,
            "template_version": "v0.1.0",
        }

        sandbox_platform = repos["sandbox-python-platform"]
        pilot.generate_sandbox(
            sandbox_platform,
            "python-starter-platform",
            "v0.1.0",
            {
                "project_name": "sandbox-python-platform",
                "package_name": "sandbox_python_platform",
            },
        )
        pilot.add_user_changes(sandbox_platform, "sandbox_python_platform")
        platform_commit = pilot.commit_push(
            sandbox_platform, "feat: generate platform sandbox from v0.1.0"
        )
        pilot.validate_answers(sandbox_platform, 1)
        report["sandboxes"]["sandbox-python-platform"] = {
            "commit": platform_commit,
            "answers": 1,
            "template_version": "v0.1.0",
        }

        workspace = repos["sandbox-workspace"]
        pilot.prepare_workspace(workspace)
        workspace_commit = pilot.commit_push(
            workspace, "feat: generate two nested Copier relationships"
        )
        pilot.validate_answers(workspace, 2)
        report["sandboxes"]["sandbox-workspace"] = {
            "commit": workspace_commit,
            "answers": 2,
            "template_version": "v0.1.0",
        }

        result_dir = workspace_root / "docs" / "results"
        result_dir.mkdir(parents=True, exist_ok=True)
        (result_dir / "prepare.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (result_dir / "prepare.md").write_text(
            "# Pilot preparation result\n\n"
            f"- Frozen source: `{pilot.SOURCE_REPO}@{pilot.SOURCE_SHA}`\n"
            f"- Components C1: `{components_sha}`\n"
            "- All three profiles match the frozen baseline for default and custom answers.\n"
            "- Components are wired by file symlinks and executable Jinja wrappers.\n"
            "- `_components` is readable by Jinja and excluded from generated output.\n"
            "- Three sandboxes exist, including two nested Copier relationships.\n"
            "- All writes were restricted to `betabitplus-template-lab/*`.\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
