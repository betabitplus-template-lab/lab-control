"""Config lifecycle integration tests.

Why:
    Verifies that public config construction, installation, and explicit
    snapshot resolution compose without relying on private imports.

Covers:
    Area: public config lifecycle
    Behavior: invalid install rejection and explicit snapshot readback
    Interface: top-level `get_config(...)` and `install_config(...)`

Checks:
    If a caller installs a non-config object, then installation fails at the
    public boundary.
    If a caller passes an explicit config snapshot, then `get_config(...)`
    returns that snapshot unchanged.
"""

from __future__ import annotations

import pytest

from [[[ package_name ]]] import (
    [[[ config_class_name ]]],
    get_config,
    install_config,
)

# =============================================================================
# Tests
# =============================================================================


def test_install_config_rejects_wrong_type() -> None:
    """The config lifecycle rejects unsupported config objects."""
    with pytest.raises(TypeError, match=r"install_config\(\) expects"):
        install_config(object())


def test_get_config_accepts_explicit_snapshot() -> None:
    """Explicit config snapshots can bypass the installed global snapshot."""
    config = [[[ config_class_name ]]]()

    assert get_config(config) is config
