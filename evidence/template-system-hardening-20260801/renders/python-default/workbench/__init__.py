"""Developer workbench entrypoints.

Why:
    Holds executable documentation and isolated feature-development scripts
    without changing shipped runtime code.

When to use:
    Imported automatically when running a workbench script in module mode, for
    example `uv run python -m workbench.group.script`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from py_lib_testkit import configure_direct_module_process

_PACKAGE_ROOT = Path(__file__).resolve().parent


def _select_main_file() -> str | None:
    """Choose one real path inside `workbench/` for direct-run setup."""
    candidates = (
        getattr(sys.modules.get("__main__"), "__file__", None),
        (sys.argv[0] if sys.argv else None),
    )
    for candidate in candidates:
        if not isinstance(candidate, str) or not candidate:
            continue
        try:
            candidate_path = Path(candidate).resolve()
            candidate_path.relative_to(_PACKAGE_ROOT)
        except (OSError, ValueError):
            continue
        return str(candidate_path)
    return None


configure_direct_module_process(
    main_file=_select_main_file(),
    package_root=_PACKAGE_ROOT,
)
