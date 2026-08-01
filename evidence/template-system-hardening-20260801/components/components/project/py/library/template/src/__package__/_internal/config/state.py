"""Runtime config snapshot state for [[[ project_title_lower ]]].

Why:
    Keeps process-wide config construction and install/read helpers inside the
    private config implementation.
"""

from __future__ import annotations

from threading import RLock

from py_lib_runtime import get_logger
[[[ "\n" if ((template_profile if template_profile is defined else "python-lib-standard") != "python-starter-platform") else "" ]]]from [[[ package_name ]]]._internal.config.assembly import (
    build_default_config,
)
from [[[ package_name ]]]._internal.config.models import (
    [[[ config_class_name ]]],
)
from [[[ package_name ]]]._internal.config.validation import (
    validate_config,
)

_installed_config: [[[ config_class_name ]]] = build_default_config()
_config_lock = RLock()
logger = get_logger(__name__)


def get_config(
    config: [[[ config_class_name ]]] | None = None,
) -> [[[ config_class_name ]]]:
    """Return a validated runtime configuration snapshot."""
    if config is not None:
        return config
    with _config_lock:
        return _installed_config


def install_config(config: object) -> [[[ config_class_name ]]]:
    """Install a validated runtime configuration snapshot."""
    if not isinstance(config, [[[ config_class_name ]]]):
[[% if (template_profile if template_profile is defined else "python-lib-standard") == "python-starter-platform" %]]
        msg = f"install_config() expects a {[[[ config_class_name ]]].__name__} instance."
[[% else %]]
        msg = f"install_config() expects a {[[[ config_class_name ]]].__name__} instance."
[[% endif %]]
        raise TypeError(msg)

    validate_config(config)
    global _installed_config  # noqa: PLW0603
    with _config_lock:
        _installed_config = config

    _clear_runtime_config_caches()
    logger.info(
        "Configuration installed",
        event_type="[[[ package_name ]]].config.runtime.installed",
    )
    return config


def _clear_runtime_config_caches() -> None:
    """Clear runtime objects that captured the previous config snapshot."""
