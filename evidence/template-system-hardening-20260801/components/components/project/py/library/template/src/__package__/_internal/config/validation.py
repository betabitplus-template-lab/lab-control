"""Runtime config validation helpers for [[[ project_title_lower ]]].

Why:
    Centralizes config normalization and invariant checks before snapshots are
    constructed or installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from [[[ package_name ]]]._internal.config.models import (
        [[[ config_class_name ]]],
    )


def validate_config(config: [[[ config_class_name ]]]) -> None:
    """Validate one runtime config snapshot."""
    _ = config
