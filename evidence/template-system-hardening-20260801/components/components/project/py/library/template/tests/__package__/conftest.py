"""Package-specific pytest fixtures for [[[ project_title_lower ]]]."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from [[[ package_name ]]] import (
    [[[ config_class_name ]]],
    install_config,
)


@pytest.fixture(autouse=True)
def reset_installed_config() -> Iterator[None]:
    """Reset process-wide config around each package test."""
    install_config([[[ config_class_name ]]]())
    try:
        yield
    finally:
        install_config([[[ config_class_name ]]]())
