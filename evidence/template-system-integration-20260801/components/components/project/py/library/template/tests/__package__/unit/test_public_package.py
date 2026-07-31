"""Public package boundary unit tests.

Why:
    Protects the initial supported top-level imports before real public
    behavior slices are added.

Covers:
    Area: public package boundary
    Behavior: exports, package-specific errors, config helpers, version metadata
    Interface: top-level `[[[ package_name ]]]`

Checks:
    If a name appears in `__all__`, then it resolves on the top-level package.
    If callers use public errors and config helpers, then the top-level package
    exposes the configured public boundary.
    If package metadata is imported, then `__version__` is available.
"""

from __future__ import annotations

import [[[ package_name ]]] as package
from [[[ package_name ]]] import (
    InvalidConfigValueError,
    [[[ config_class_name ]]] as Config,
    [[[ error_class_name ]]] as PackageError,
)

# =============================================================================
# Tests
# =============================================================================


def test_public_exports_resolve() -> None:
    """All supported public names are exported by the top-level package."""
    for name in package.__all__:
        assert hasattr(package, name)


def test_public_exception_is_package_specific() -> None:
    """The package exposes one public exception base."""
    assert issubclass(PackageError, Exception)


def test_public_config_exports_resolve() -> None:
    """The package exposes the shared config lifecycle."""
    installed = package.install_config(Config())

    assert package.get_config().__class__ is Config
    assert installed.__class__ is Config


def test_invalid_config_error_is_public() -> None:
    """The package exposes a config-specific public error."""
    error = InvalidConfigValueError(
        field="field",
        value={"secret": "redacted"},
        reason="bad",
    )

    assert isinstance(error, PackageError)
    assert "Invalid config value for field" in str(error)


def test_version_is_available() -> None:
    """The package exposes distribution metadata."""
    assert package.__version__
