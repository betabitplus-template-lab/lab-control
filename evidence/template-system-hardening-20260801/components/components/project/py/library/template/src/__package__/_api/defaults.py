"""Built-in default declarations for [[[ project_title_lower ]]].

Why:
    Keeps shared built-in defaults in one declarative place instead of
    scattering them across runtime code.

How:
    Add `DEFAULT_*` values here when real config fields or runtime catalogs
    exist. Config assembly should validate, copy, and freeze those declarations
    before runtime work begins.
"""

from __future__ import annotations
