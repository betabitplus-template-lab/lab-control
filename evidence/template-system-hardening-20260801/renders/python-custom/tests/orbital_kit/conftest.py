"""Package-specific pytest fixtures for orbital kit."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from orbital_kit import (
    OrbitalKitConfig,
    install_config,
)


@pytest.fixture(autouse=True)
def reset_installed_config() -> Iterator[None]:
    """Reset process-wide config around each package test."""
    install_config(OrbitalKitConfig())
    try:
        yield
    finally:
        install_config(OrbitalKitConfig())
