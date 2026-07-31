"""Private implementation root for sample lib.

Why:
    Provides narrow private-root entrypoints used by `_api` facades so facade
    modules do not import deep implementation modules.
"""

from __future__ import annotations

from sample_lib._internal.config import (
    SampleLibConfig as _Config,
    get_config as get_config,
    install_config as install_config,
)

SampleLibConfig = _Config
