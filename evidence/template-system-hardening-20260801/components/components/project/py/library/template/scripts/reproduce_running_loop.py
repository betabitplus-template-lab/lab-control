#!/usr/bin/env python3
"""Run a module while an asyncio event loop is active."""

from __future__ import annotations

import argparse
import asyncio
import runpy
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module")
    parser.add_argument("module_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    for path in (root, root / "src"):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)

    original_argv = sys.argv[:]
    sys.argv = [args.module, *args.module_args]

    async def execute() -> None:
        runpy.run_module(args.module, run_name="__main__")

    try:
        asyncio.run(execute())
    finally:
        sys.argv = original_argv
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
