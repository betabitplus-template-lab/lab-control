"""Public exceptions for [[[ project_title_lower ]]].

Why:
    Keeps caller-facing failure types separate from private runtime details.
"""

from __future__ import annotations

from py_lib_runtime import preview_value


class [[[ error_class_name ]]](Exception):
    """Base class for package-specific public errors."""


class InvalidConfigValueError([[[ error_class_name ]]], ValueError):
    """Raised when public config input violates a config invariant."""

    def __init__(self, *, field: str, value: object, reason: str) -> None:
        """Build a caller-safe config validation message."""
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(
            f"Invalid config value for {field}: {preview_value(value)} ({reason}).",
        )
