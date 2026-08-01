"""Runtime configuration package for orbital kit.

Why:
    Owns validated immutable configuration snapshots for private runtime
    instances.
"""

from __future__ import annotations

from orbital_kit._internal.config.assembly import (
    build_default_config as build_default_config,
)
from orbital_kit._internal.config.models import (
    OrbitalKitConfig as _Config,
)
from orbital_kit._internal.config.state import (
    get_config as get_config,
    install_config as install_config,
)
from orbital_kit._internal.config.validation import (
    validate_config as validate_config,
)

OrbitalKitConfig = _Config
