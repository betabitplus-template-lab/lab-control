"""Supported public package entrypoint for `sample_lib`.

Why:
    Exposes the stable public surface from one import boundary.

What belongs here:
    Re-exports of facade functions/classes, public DTOs, config objects,
    vocabulary types, public exceptions, and package version.

What does not belong here:
    Raw defaults, private runtime helpers, adapters, stores, or other
    implementation details.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from sample_lib._api.config import (
    SampleLibConfig,
    get_config,
    install_config,
)
from sample_lib._api.errors import (
    InvalidConfigValueError,
    SampleLibError,
)

try:
    __version__ = version("sample-lib")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+local"

__all__ = [
    "InvalidConfigValueError",
    "SampleLibConfig",
    "SampleLibError",
    "__version__",
    "get_config",
    "install_config",
]
