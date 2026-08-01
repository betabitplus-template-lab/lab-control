"""Supported public package entrypoint for `[[[ package_name ]]]`.

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

from [[[ package_name ]]]._api.config import (
    [[[ config_class_name ]]],
    get_config,
    install_config,
)
from [[[ package_name ]]]._api.errors import (
    InvalidConfigValueError,
    [[[ error_class_name ]]],
)

try:
    __version__ = version("[[[ project_name ]]]")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+local"

__all__ = [
    "InvalidConfigValueError",
    "[[[ config_class_name ]]]",
    "[[[ error_class_name ]]]",
    "__version__",
    "get_config",
    "install_config",
]
