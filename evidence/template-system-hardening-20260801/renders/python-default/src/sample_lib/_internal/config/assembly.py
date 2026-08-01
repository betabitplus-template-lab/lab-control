"""Built-in config assembly for sample lib.

Why:
    Converts public default declarations into validated private config
    snapshots before runtime work begins.
"""

from __future__ import annotations

from sample_lib._internal.config.models import (
    SampleLibConfig,
)
from sample_lib._internal.config.validation import (
    validate_config,
)


def build_default_config() -> SampleLibConfig:
    """Assemble and validate the built-in runtime config snapshot."""
    config = SampleLibConfig()
    validate_config(config)
    return config
