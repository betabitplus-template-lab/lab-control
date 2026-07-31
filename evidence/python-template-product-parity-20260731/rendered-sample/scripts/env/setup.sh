#!/usr/bin/env bash
set -euo pipefail

echo "Setting up development environment..."

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

# Install dev dependencies (creates/updates .venv)
uv sync --group dev

# Install every hook stage declared by default_install_hook_types
uv run pre-commit install

echo "Setup complete! All pre-commit hooks installed."
