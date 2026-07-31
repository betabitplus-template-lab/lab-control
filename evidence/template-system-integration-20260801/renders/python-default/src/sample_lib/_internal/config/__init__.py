"""Runtime configuration package for sample lib.

Why:
    Owns validated immutable configuration snapshots for private runtime
    instances.
"""

from __future__ import annotations

from sample_lib._internal.config.assembly import (
    build_default_config as build_default_config,
)
from sample_lib._internal.config.models import (
    SampleLibConfig as _Config,
)
from sample_lib._internal.config.state import (
    get_config as get_config,
    install_config as install_config,
)
from sample_lib._internal.config.validation import (
    validate_config as validate_config,
)

SampleLibConfig = _Config
