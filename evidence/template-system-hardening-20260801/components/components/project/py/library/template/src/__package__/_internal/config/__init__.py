"""Runtime configuration package for [[[ project_title_lower ]]].

Why:
    Owns validated immutable configuration snapshots for private runtime
    instances.
"""

from __future__ import annotations

from [[[ package_name ]]]._internal.config.assembly import (
    build_default_config as build_default_config,
)
from [[[ package_name ]]]._internal.config.models import (
    [[[ config_class_name ]]] as _Config,
)
from [[[ package_name ]]]._internal.config.state import (
    get_config as get_config,
    install_config as install_config,
)
from [[[ package_name ]]]._internal.config.validation import (
    validate_config as validate_config,
)

[[[ config_class_name ]]] = _Config
