"""Package-specific pytest fixtures for sample lib."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from sample_lib import (
    SampleLibConfig,
    install_config,
)


@pytest.fixture(autouse=True)
def reset_installed_config() -> Iterator[None]:
    """Reset process-wide config around each package test."""
    install_config(SampleLibConfig())
    try:
        yield
    finally:
        install_config(SampleLibConfig())
