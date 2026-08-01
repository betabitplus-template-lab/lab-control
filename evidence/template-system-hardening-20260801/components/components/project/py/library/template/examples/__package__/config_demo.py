# %%
"""Runnable public config example for [[[ project_title_lower ]]].

Run from the repository root:
    uv run python examples/[[[ package_name ]]]/config_demo.py
"""

from __future__ import annotations

from [[[ package_name ]]] import (
    [[[ config_class_name ]]],
    get_config,
    install_config,
)


def main() -> None:
    """Install and read the public config snapshot."""
    config = install_config([[[ config_class_name ]]]())
    active_config = get_config()
    print(f"active_config: {type(active_config).__name__}")
    print(f"same_object: {active_config is config}")


if __name__ == "__main__":
    main()
