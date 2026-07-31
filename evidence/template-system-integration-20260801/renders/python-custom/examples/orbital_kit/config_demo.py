# %%
"""Runnable public config example for orbital kit.

Run from the repository root:
    uv run python examples/orbital_kit/config_demo.py
"""

from __future__ import annotations

from orbital_kit import (
    OrbitalKitConfig,
    get_config,
    install_config,
)


def main() -> None:
    """Install and read the public config snapshot."""
    config = install_config(OrbitalKitConfig())
    active_config = get_config()
    print(f"active_config: {type(active_config).__name__}")
    print(f"same_object: {active_config is config}")


if __name__ == "__main__":
    main()
