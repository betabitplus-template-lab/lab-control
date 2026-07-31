"""Built-in config assembly for orbital kit.

Why:
    Converts public default declarations into validated private config
    snapshots before runtime work begins.
"""

from __future__ import annotations

from orbital_kit._internal.config.models import (
    OrbitalKitConfig,
)
from orbital_kit._internal.config.validation import (
    validate_config,
)


def build_default_config() -> OrbitalKitConfig:
    """Assemble and validate the built-in runtime config snapshot."""
    config = OrbitalKitConfig()
    validate_config(config)
    return config
