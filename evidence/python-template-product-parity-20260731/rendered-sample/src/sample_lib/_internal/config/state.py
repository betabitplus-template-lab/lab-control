"""Runtime config snapshot state for sample lib.

Why:
    Keeps process-wide config construction and install/read helpers inside the
    private config implementation.
"""

from __future__ import annotations

from threading import RLock

from py_lib_runtime import get_logger

from sample_lib._internal.config.assembly import (
    build_default_config,
)
from sample_lib._internal.config.models import (
    SampleLibConfig,
)
from sample_lib._internal.config.validation import (
    validate_config,
)

_installed_config: SampleLibConfig = build_default_config()
_config_lock = RLock()
logger = get_logger(__name__)


def get_config(
    config: SampleLibConfig | None = None,
) -> SampleLibConfig:
    """Return a validated runtime configuration snapshot."""
    if config is not None:
        return config
    with _config_lock:
        return _installed_config


def install_config(config: object) -> SampleLibConfig:
    """Install a validated runtime configuration snapshot."""
    if not isinstance(config, SampleLibConfig):
        msg = f"install_config() expects a {SampleLibConfig.__name__} instance."
        raise TypeError(msg)

    validate_config(config)
    global _installed_config  # noqa: PLW0603
    with _config_lock:
        _installed_config = config

    _clear_runtime_config_caches()
    logger.info(
        "Configuration installed",
        event_type="sample_lib.config.runtime.installed",
    )
    return config


def _clear_runtime_config_caches() -> None:
    """Clear runtime objects that captured the previous config snapshot."""
