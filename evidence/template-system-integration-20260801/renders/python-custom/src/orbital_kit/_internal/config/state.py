"""Runtime config snapshot state for orbital kit.

Why:
    Keeps process-wide config construction and install/read helpers inside the
    private config implementation.
"""

from __future__ import annotations

from threading import RLock

from py_lib_runtime import get_logger

from orbital_kit._internal.config.assembly import (
    build_default_config,
)
from orbital_kit._internal.config.models import (
    OrbitalKitConfig,
)
from orbital_kit._internal.config.validation import (
    validate_config,
)

_installed_config: OrbitalKitConfig = build_default_config()
_config_lock = RLock()
logger = get_logger(__name__)


def get_config(
    config: OrbitalKitConfig | None = None,
) -> OrbitalKitConfig:
    """Return a validated runtime configuration snapshot."""
    if config is not None:
        return config
    with _config_lock:
        return _installed_config


def install_config(config: object) -> OrbitalKitConfig:
    """Install a validated runtime configuration snapshot."""
    if not isinstance(config, OrbitalKitConfig):
        msg = f"install_config() expects a {OrbitalKitConfig.__name__} instance."
        raise TypeError(msg)

    validate_config(config)
    global _installed_config  # noqa: PLW0603
    with _config_lock:
        _installed_config = config

    _clear_runtime_config_caches()
    logger.info(
        "Configuration installed",
        event_type="orbital_kit.config.runtime.installed",
    )
    return config


def _clear_runtime_config_caches() -> None:
    """Clear runtime objects that captured the previous config snapshot."""
