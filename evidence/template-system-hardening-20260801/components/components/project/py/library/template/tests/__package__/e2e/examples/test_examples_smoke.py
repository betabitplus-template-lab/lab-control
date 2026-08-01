# %%
"""Runnable examples smoke tests.

Why:
    Keeps committed public API examples from drifting while leaving behavioral
    assertions in unit, integration, and focused e2e tests.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.e2e_behavior,
    pytest.mark.hermetic,
]

_REPO_ROOT = Path(__file__).resolve().parents[4]
_EXAMPLES_ROOT = _REPO_ROOT / "examples" / "[[[ package_name ]]]"
_EXAMPLE_SCRIPTS = tuple(
    path for path in sorted(_EXAMPLES_ROOT.rglob("*.py")) if path.name != "__init__.py"
)


@pytest.mark.parametrize("script_path", _EXAMPLE_SCRIPTS)
def test_example_script_runs(script_path: Path) -> None:
    """Runnable example scripts exit successfully."""
    repo_root = _repo_root()
    result = subprocess.run(
        [sys.executable, script_path.relative_to(repo_root).as_posix()],
        cwd=repo_root,
        env=_example_env(repo_root),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def _repo_root() -> Path:
    """Return the generated repository root."""
    return _REPO_ROOT


def _example_env(repo_root: Path) -> dict[str, str]:
    """Return a subprocess environment that can import local project sources."""
    env = os.environ.copy()
    pythonpath = str(repo_root / "src")
    if env.get("PYTHONPATH"):
        pythonpath = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
    env["PYTHONPATH"] = pythonpath
    return env
