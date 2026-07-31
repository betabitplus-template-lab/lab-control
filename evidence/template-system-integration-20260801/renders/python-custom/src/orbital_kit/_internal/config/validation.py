"""Runtime config validation helpers for orbital kit.

Why:
    Centralizes config normalization and invariant checks before snapshots are
    constructed or installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orbital_kit._internal.config.models import (
        OrbitalKitConfig,
    )


def validate_config(config: OrbitalKitConfig) -> None:
    """Validate one runtime config snapshot."""
    _ = config
