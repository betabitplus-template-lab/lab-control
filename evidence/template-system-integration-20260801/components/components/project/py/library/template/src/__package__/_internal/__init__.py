"""Private implementation root for [[[ project_title_lower ]]].

Why:
    Provides narrow private-root entrypoints used by `_api` facades so facade
    modules do not import deep implementation modules.
"""

from __future__ import annotations

from [[[ package_name ]]]._internal.config import (
    [[[ config_class_name ]]] as _Config,
    get_config as get_config,
    install_config as install_config,
)

[[[ config_class_name ]]] = _Config
