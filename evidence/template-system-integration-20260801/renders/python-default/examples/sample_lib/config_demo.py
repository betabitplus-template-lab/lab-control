# %%
"""Runnable public config example for sample lib.

Run from the repository root:
    uv run python examples/sample_lib/config_demo.py
"""

from __future__ import annotations

from sample_lib import (
    SampleLibConfig,
    get_config,
    install_config,
)


def main() -> None:
    """Install and read the public config snapshot."""
    config = install_config(SampleLibConfig())
    active_config = get_config()
    print(f"active_config: {type(active_config).__name__}")
    print(f"same_object: {active_config is config}")


if __name__ == "__main__":
    main()
