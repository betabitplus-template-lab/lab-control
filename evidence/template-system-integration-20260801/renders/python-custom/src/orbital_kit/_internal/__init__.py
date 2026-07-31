"""Private implementation root for orbital kit.

Why:
    Provides narrow private-root entrypoints used by `_api` facades so facade
    modules do not import deep implementation modules.
"""

from __future__ import annotations

from orbital_kit._internal.config import (
    OrbitalKitConfig as _Config,
    get_config as get_config,
    install_config as install_config,
)

OrbitalKitConfig = _Config
