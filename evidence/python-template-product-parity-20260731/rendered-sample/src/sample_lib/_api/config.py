"""Public config re-exports.

Why:
    Keeps config names behind the `_api` facade while `_internal` owns config
    models, validation, runtime default assembly, and snapshot state.
"""

from __future__ import annotations

# pyright: reportUnusedImport=false
from sample_lib._internal import (  # noqa: F401
    SampleLibConfig,
    get_config,
    install_config,
)
