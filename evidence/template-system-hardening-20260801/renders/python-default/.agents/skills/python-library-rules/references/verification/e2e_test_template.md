---
name: e2e-test-template
description: Template for executable Python end-to-end test files. Use when you need a standard file shape for scenario-driven e2e tests under tests/.../e2e/.
---

# E2E Test Template

## Overview

Use this template for executable Python e2e test files.

Use the e2e-specific docstring pattern from
`references/core/docstring_template.md`.

## When To Use

Use this template for executable e2e test files under `tests/.../e2e/`.

When the project uses `architecture/concepts/` as the primary vertical-slice
grouping, keep each e2e script in the concept-aligned folder for the slice it
proves.

## File Shape

Keep this top-level order in every file:

1. file header docstring
2. imports
3. `pytestmark`
4. `Scenario`
5. `Helpers`
6. `Pipeline`
7. `Assertions`
8. `Tests`
9. `Demo (Manual Execution)`

## Standard Section Titles

Use only these top-level section titles:

- `Scenario`
- `Helpers`
- `Pipeline`
- `Assertions`
- `Tests`
- `Demo (Manual Execution)`

## Core Rules (Testing)

- Use `references/verification/tests_routing_pattern.md` for test tree placement.
- Hermetic replay for external API calls.
- Import product behavior only from the product's public top-level package in
  e2e tests. Shared test infrastructure may come from top-level
  `py_lib_testkit`.
- Do not patch or monkeypatch library internals in e2e tests.
- Test-only helpers and setup must live under `tests/`, never under `src/`.
- Tests should validate public behavior, not internal implementation details.
- `main()` must run live.
- Demo runs must never replay or record VCR traffic.
- If a live demo and a replayed pytest run would produce different behavior,
  the test is wrong and must be fixed.
- Put assertions in a dedicated helper instead of spreading them through the test body.
- Keep `main()` close to the actual test flow.
- `Demo (Manual Execution)` must semantically mirror the `Assertions` section.
- Manual demo output must expose the same meaningful scenario result and verification-relevant details a human would need to confirm the test really succeeded.
- If a file asserts multiple meaningful scenarios or public outcomes, `main()` must show each of them, or clearly show an equivalent success and failure shape for every asserted behavior category.
- Manual demo output should read like a short narrative for a non-specialist reader: what is being tested, why it matters, what happened step by step, and why the result counts as success.
- Prefer readable explanation over raw logs. Keep technical evidence, but frame it with enough context that a PM can understand the scenario without opening the code.
- pytest-based hermetic runs replay committed cassettes.
- recording or forced replay is enabled explicitly.
- Runnable e2e scripts must also work in already-running loop environments.
- Async test entrypoints must use the top-level
  `py_lib_testkit.run_async(...)` helper instead of calling
  `asyncio.run(...)` directly in Ternforge-managed Python libraries.

## Rules

- Keep the top-level section order fixed.
- Write docstring `Checks` lines in explicit `If <condition>, then <consequence>.`
  form so the proving condition and the expected outcome stay obvious.
- Make docstring `Checks` cover every meaningful assertion or assertion
  cluster from the file's `Assertions` section.
- Keep `Assertions` readable as a short walkthrough rather than a silent
  predicate dump.
- Keep empty standard sections explicit with a short one-line note instead of
  silently implying missing layout.
- Run executable e2e files in module mode so shared setup comes from
  `tests.<project>.e2e`.

## Section Notes

`Scenario` holds all fixed case data. Put the real inputs first, then expected
outputs, output paths, or other fixed expectations.

`Assertions` should read like a short walkthrough, not a silent pile of
predicates. For non-obvious scenarios, add short comments that explain what
each assertion is proving and why that check matters.

`Helpers`, `Pipeline`, `Tests`, and `Demo (Manual Execution)` should follow the
same idea when the scenario is not obvious. A reader should be able to follow
the intended failure, recovery, or boundary behavior without reverse-engineering
the whole file.

If a standard section would otherwise be empty, keep the section and make that
explicit with a short one-line note.

Example:

```python
# =============================================================================
# Helpers
# =============================================================================

# No local helpers for this scenario.
```

Very short assertion-style illustration:

```python
def assert_pipeline_response(response: ImageReport) -> None:
    # First prove the title is really present.
    assert response.title.strip()

    # Then prove the summary is not an empty stub.
    assert response.summary.strip()

    # Finally, check the exact normalized tag count the scenario promises.
    assert len(normalize_tags(response.tags)) == _EXPECTED_TAG_COUNT
```

Very short full-flow illustration:

```python
def run_pipeline(*, image_path: Path) -> ImageReport:
    # This is the one public call the scenario is really about.
    return analyze_image(
        image_path=image_path,
        instructions=_INSTRUCTIONS,
        schema=ImageReport,
    )


def test_pipeline() -> None:
    # First run the public flow exactly as a user would.
    response = run_pipeline(image_path=_INPUT_IMAGE)

    # Then validate the contract in one dedicated assertion helper.
    assert_pipeline_response(response)
```

## Template

Use the file below as the reference layout.

```python
# %%
"""Image analysis workflow e2e.

Why:
    Verifies that the public image-analysis entry point accepts an image input
    and returns normalized structured output.

Covers:
    Area: image analysis workflow
    Behavior: image input, structured output
    Interface: public function call with schema-driven output

Checks:
    If the public call succeeds, then the response contains a non-empty title
    and summary.
    If the structured output is normalized correctly, then the response
    returns exactly 3 normalized tags.

Notes:
    Add only when runtime prerequisites or live-run caveats matter.

Examples:
    Run manually:
        uv run python -m tests.project.e2e.group.test_file

    Run as test:
        pytest path/to/test_file.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from IPython.display import Image, display
from pydantic import BaseModel, Field

from py_lib_testkit import console, require_vcr_cassette_or_record_mode
from your_package import analyze_image

pytestmark = [
    pytest.mark.e2e_contract,
    pytest.mark.cap_image,
    pytest.mark.cap_structured,
]


# =============================================================================
# Scenario
# =============================================================================

# Real Inputs
_INPUT_IMAGE = Path("tests/data/sample_image.png")
_INSTRUCTIONS = [
    "Inspect the image.",
    "Return JSON with a short title, a one-sentence summary, and exactly 3 tags.",
]

# Expected Outputs
# Keep deterministic expectations close to the inputs they explain.
_EXPECTED_TAG_COUNT = 3


# =============================================================================
# Helpers
# =============================================================================


# Local helper types
class ImageReport(BaseModel):
    """Structured output used by this scenario."""

    title: str = Field(min_length=1)
    summary: str = Field(min_length=10)
    tags: list[str] = Field(min_length=3, max_length=3)


def normalize_tags(tags: list[str]) -> list[str]:
    """Normalize tags for stable assertions."""
    return sorted(tag.strip().lower() for tag in tags)


def format_result_for_demo(result: ImageReport) -> str:
    """Format the result for readable demo output."""
    return json.dumps(result.model_dump(), indent=2)


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, image_path: Path) -> ImageReport:
    """Run the public end-to-end flow."""
    # This function should read like the real user workflow, not like test-only
    # setup scattered across multiple helpers.
    return analyze_image(
        image_path=image_path,
        instructions=_INSTRUCTIONS,
        schema=ImageReport,
    )


# =============================================================================
# Assertions
# =============================================================================


def assert_pipeline_response(response: ImageReport) -> None:
    """Assert the public response for the scenario."""
    # First prove the response contains the core user-visible fields.
    assert response.title.strip()
    assert response.summary.strip()

    # Then prove the structured shape matches the contract for this scenario.
    assert len(normalize_tags(response.tags)) == _EXPECTED_TAG_COUNT


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.hermetic
@pytest.mark.vcr
def test_pipeline() -> None:
    """Verify the pipeline runs successfully."""
    require_vcr_cassette_or_record_mode(test_file=__file__, test_name="test_pipeline")

    # First execute the public flow exactly once.
    response = run_pipeline(image_path=_INPUT_IMAGE)

    # Then keep all contract checks in the dedicated assertion helper.
    assert_pipeline_response(response)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the demo flow for manual execution."""
    console.rule("[header]E2E Demo[/]")
    display(Image(filename=str(_INPUT_IMAGE)))

    # Run the same public flow as the automated test.
    response = run_pipeline(image_path=_INPUT_IMAGE)

    # Reuse the same assertion helper so the manual demo and pytest stay aligned.
    assert_pipeline_response(response)
    console.print(format_result_for_demo(response))


if __name__ == "__main__":
    main()

# %%
```
