"""Built-in config assembly for [[[ project_title_lower ]]].

Why:
    Converts public default declarations into validated private config
    snapshots before runtime work begins.
"""

from __future__ import annotations

from [[[ package_name ]]]._internal.config.models import (
    [[[ config_class_name ]]],
)
from [[[ package_name ]]]._internal.config.validation import (
    validate_config,
)


def build_default_config() -> [[[ config_class_name ]]]:
    """Assemble and validate the built-in runtime config snapshot."""
    config = [[[ config_class_name ]]]()
    validate_config(config)
    return config
