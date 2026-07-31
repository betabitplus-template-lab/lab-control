---
name: test-file-template
description: Template for ordinary pytest verification files. Use when you need one reusable file shape for unit, integration, or property-based tests under tests/.
---

# Test File Template

## Overview

Use this template for non-e2e pytest files under `tests/`.

This is the shared file-shape reference for:

- unit tests
- integration tests
- property-based tests

Use the e2e-specific template only for replay-backed scenario scripts under
`tests/.../e2e/`.

Use the Python docstring pattern from `references/core/docstring_template.md`.

## When To Use

Use this template when the file is a normal pytest module rather than an
executable e2e scenario or a live workbench script.

Use this template when you want one consistent shape for fast deterministic
tests, controlled integration checks, or invariant-driven generated tests.

## File Shape

Keep this top-level order, using only the sections the file genuinely needs:

1. file header docstring
2. imports
3. fixed `pytestmark` or module-level config when needed
4. `Scenario` or `Strategies`
5. `Fixtures`
6. `Helpers`
7. `Assertions`
8. `Properties` and/or `Tests`

## Standard Section Titles

Use only these top-level section titles when they are needed:

- `Scenario`
- `Strategies`
- `Fixtures`
- `Helpers`
- `Assertions`
- `Properties`
- `Tests`

## Rules

- Use only the sections the file genuinely needs.
- Keep shared fixtures and builders out of the file when they belong in
  top-level `py_lib_testkit` helpers or `tests/<project>/support/`.
- Keep `Assertions` readable as a short walkthrough of the public rule being
  protected.
- Keep `Properties` before `Tests` when the file mixes generated checks with
  named examples.

## Section Notes

`Scenario` holds fixed example inputs, expected outputs, or named boundary
cases. Prefer it for unit or integration files with explicit cases.

`Strategies` holds Hypothesis strategies and related generated-input helpers.
Prefer it for property-based files. Keep the generated domain meaningful and
small enough to shrink well.

`Fixtures` holds local pytest fixtures that are specific to the file. Shared
cross-project fixtures and helpers should come from top-level `py_lib_testkit`
in Ternforge-managed Python libraries; package-specific builders should live under
`tests/<project>/support/` instead.

`Helpers` holds small builders, formatters, comparison helpers, and local
support code that make the test bodies read clearly.

`Assertions` should read like a short walkthrough. Add short comments when the
check is not obvious so the reader can see what public rule is being protected
and why it matters.

For non-obvious tests, add a bit more comment guidance than you would in a
tiny unit test so the file reads like a compact assertion walkthrough rather
than a bare assertion dump. When choosing between ultra-minimal comments and a
few short useful "why" comments, prefer the latter.

`Properties` is for invariant-driven generated tests. Use it when the file has
Hypothesis-driven checks and you want those properties to be easy to scan
separately from named examples.

Property-based files usually need a bit more commentary than example-only
files because generated inputs can hide test intent if the invariant is not
explained clearly. Prefer a few extra intent comments over making the reader
reverse-engineer the property from the assertions alone.

`Tests` is for ordinary example-based pytest cases. Use it for named boundary
checks, narrow regressions, or small integration flows.

If a file mixes generated properties with named examples, keep both sections in
that order: `Properties` first, then `Tests`.

If a standard section would otherwise be empty, omit it instead of keeping a
decorative placeholder.

## Layer Notes

For unit tests:

- prefer pure functions, public DTOs, and small deterministic boundaries
- avoid broad environment setup
- for public config behavior, import from the top-level package and cover
  install/read behavior, non-config `TypeError`, and cache invalidation when
  runtime objects capture installed snapshots

For integration tests:

- keep the test focused on one meaningful collaboration boundary
- prefer public interfaces and realistic construction over mocking every layer

For property-based tests:

- keep public-contract property files separate from internal property files
- for public-contract property files, keep the invariant public and stable
- for public-contract property files, import only from the supported top-level
  package boundary
- for public-contract property files, do not import `_internal` modules
- for internal property files, keep the private invariant explicit and place
  the file in a separate internal property group instead of mixing it with
  public-contract files
- generate valid inputs intentionally instead of producing random invalid noise

## Template

Use the file below as the reference layout.

```python
"""Example deterministic and generated verification file.

Why:
    Protects stable public behavior with a mix of generated invariants and
    small named boundary examples.

Covers:
    Area: public request helpers
    Behavior: omission semantics, preserved explicit values
    Interface: public DTO construction and expansion helpers

Checks:
    If callers pass explicit non-null values, then those values are preserved.
    If callers omit optional values, then those values stay omitted.
    If callers pass named invalid inputs, then validation fails at the public
    boundary.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from your_package import PublicBundle


# =============================================================================
# Strategies
# =============================================================================


_SAFE_TEXT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
    min_size=1,
    max_size=12,
)
_OPTIONAL_LIMIT = st.one_of(st.none(), st.integers(min_value=1, max_value=5))


# =============================================================================
# Helpers
# =============================================================================


def assert_bundle_kwargs(
    result: dict[str, object],
    *,
    limit: int | None,
    label: str | None,
) -> None:
    """Assert the public omission and preservation rules."""
    # Omitted values should stay omitted so higher-precedence layers can win.
    assert ("limit" in result) is (limit is not None)
    assert ("label" in result) is (label is not None)

    # Explicit values should survive expansion unchanged.
    if limit is not None:
        assert result["limit"] == limit
    if label is not None:
        assert result["label"] == label


# =============================================================================
# Properties
# =============================================================================


@given(limit=_OPTIONAL_LIMIT, label=st.one_of(st.none(), _SAFE_TEXT))
def test_public_bundle_as_kwargs_preserves_explicit_values(
    *,
    limit: int | None,
    label: str | None,
) -> None:
    """Generated inputs should preserve the public omission contract."""
    # First build the public bundle exactly as a caller would.
    bundle = PublicBundle(limit=limit, label=label)

    # Then expand it through the public helper whose semantics we care about.
    result = bundle.as_kwargs()

    # This is the core semantic check for the helper: omission should stay
    # omission, and explicit values should keep their exact caller meaning.
    assert_bundle_kwargs(result, limit=limit, label=label)


# =============================================================================
# Tests
# =============================================================================


def test_public_bundle_rejects_negative_limit() -> None:
    """Named boundary example for one invalid caller input."""
    # Keep named boundary examples short, but still explain why this specific
    # failure matters at the public API edge.
    with pytest.raises(ValueError, match="positive"):
        PublicBundle(limit=-1)
```
