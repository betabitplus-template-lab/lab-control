"""Public config snapshot property tests.

Why:
    Protects the public config contract with property-based routing
    in the same tree structure used by mature py libraries.

Covers:
    Area: public config lifecycle
    Behavior: explicit config snapshot identity
    Interface: top-level `get_config(...)`

Checks:
    If generated inputs leave the explicit config snapshot unchanged, then
    `get_config(...)` returns that same public snapshot.
"""

from __future__ import annotations

from hypothesis import given, strategies as st

from [[[ package_name ]]] import (
    [[[ config_class_name ]]],
    get_config,
)

# =============================================================================
# Properties
# =============================================================================


@given(st.none())
def test_explicit_config_snapshot_round_trips(value: None) -> None:
    """Hypothesis inputs do not change explicit config snapshot identity."""
    _ = value
    config = [[[ config_class_name ]]]()

    assert get_config(config) is config
