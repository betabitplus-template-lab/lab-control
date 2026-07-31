# Implementation Boundaries

## Overview

This file defines the strict edit boundaries for the future implementing agent.

Most important rules:

- Only the allowed implementation paths may change during implementation.
- Current docs and tests are the contract.
- Git history is not an allowed input.

## Allowed Edit Paths

- `src/<package_name>/_internal`
- `docs/<package_name>/implementation`
- `tests/<package_name>/integration`
- `tests/<package_name>/unit`
- `tests/<package_name>/property_based/internal`

## Boundary Rules

- During implementation, only these paths may be changed:
  `src/<package_name>/_internal`,
  `docs/<package_name>/implementation`,
  `tests/<package_name>/integration`,
  `tests/<package_name>/unit`,
  `tests/<package_name>/property_based/internal`.
- Other paths must not be modified during the implementation phase.
- If a correct config cutover requires changes outside the allowed paths, such
  as thinning `_api/config.py` or updating `pyproject.toml`, record that as an
  out-of-scope prerequisite or separately authorized phase instead of changing
  it silently.
- Current docs and tests are the contract and must be followed strictly.
- Do not inspect git history or how the project used to be implemented. Plan
  and implement from the current state only.
