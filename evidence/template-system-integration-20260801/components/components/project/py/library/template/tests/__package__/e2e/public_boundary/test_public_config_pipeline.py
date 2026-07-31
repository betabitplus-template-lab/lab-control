# %%
"""[[[ project_title ]]] public config boundary scenario.

Why:
    Verifies that the top-level package API can install and read a
    runtime config snapshot end to end.

Covers:
    Area: public package boundary
    Behavior: config installation and readback
    Interface: top-level `[[[ package_name ]]]`

Checks:
    If a caller installs a config snapshot, then `get_config()` returns the same
    public snapshot through the supported top-level import boundary.

    Examples:
        Run manually:
            uv run python -m \
                tests.[[[ package_name ]]].e2e.public_boundary.test_public_config_pipeline

        Run as test:
            pytest this file directly.
"""

from __future__ import annotations

import pytest
from py_lib_testkit import console

from [[[ package_name ]]] import (
    [[[ config_class_name ]]] as Config,
    get_config,
    install_config,
)

pytestmark = [
    pytest.mark.e2e_contract,
    pytest.mark.hermetic,
]


# =============================================================================
# Scenario
# =============================================================================

# No fixed external inputs are needed for this config lifecycle scenario.


# =============================================================================
# Helpers
# =============================================================================

# No local helpers are needed; the public config object is the full scenario input.


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline() -> Config:
    """Run the public config install/read flow."""
    return install_config(Config())


# =============================================================================
# Assertions
# =============================================================================


def assert_public_config_response(config: Config) -> None:
    """Assert the public config snapshot is the installed runtime snapshot."""
    assert get_config() is config


# =============================================================================
# Tests
# =============================================================================


def test_public_config_pipeline() -> None:
    """The public config lifecycle works through the top-level package."""
    config = run_pipeline()

    assert_public_config_response(config)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the public config boundary scenario as a manual demo."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Installing a config snapshot through the public package.",
    )

    config = run_pipeline()
    assert_public_config_response(config)
    console.demo_step(
        "Observed Config",
        "The installed config is the active public runtime snapshot.",
        details=(f"config_type: {type(config).__name__}",),
    )
    console.demo_outcome("The public config boundary is wired correctly.")


if __name__ == "__main__":
    main()

# %%
