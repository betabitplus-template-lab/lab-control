---
name: workbench-script-template
description: Template for manual workbench scripts under workbench/<group>/. Use when you need a live executable probe for one concrete behavior, seam, or dependency question.
---

# Workbench Script Template

## Overview

Use this template for new files under `workbench/<group>/`.

Use the e2e-style scenario docstring pattern from
`references/core/docstring_template.md`.

## When To Use

Use this template for manual workbench scripts that isolate one real behavior,
question, or dependency seam.

## File Shape

Keep this top-level order:

1. top-of-file `# %%`
2. file docstring
3. imports
4. `Scenario`
5. `Helpers` if needed
6. `Pipeline`
7. `Demo (Manual Execution)`
8. `Expected Output`

## Standard Section Titles

Use only these top-level section titles:

- `Scenario`
- `Helpers`
- `Pipeline`
- `Demo (Manual Execution)`
- `Expected Output`

## Core Rules (Workbench)

- One script file should answer one concrete question, test one hypothesis, or isolate one feature behavior.
- If logic becomes large, reused, or shared across multiple scripts, move it into an internal helper module with a leading underscore and a specific name.
- `workbench/` is for live executable documentation and isolated feature development before logic graduates into `src/` and `tests/`.
- Keep workbench scripts independent from `src/`; do not reference project internal modules or implementation paths from workbench code.
- Shared package-level direct-run setup should live in `workbench/__init__.py`, not repeated in each script.
- Workbench scripts must run directly with `uv run python -m path.to.script`.
  In Ternforge-managed Python libraries, every workbench script must also work under
  `uv run python scripts/reproduce_running_loop.py path.to.script`.
- Async workbench entrypoints must use the top-level
  `py_lib_testkit.run_async(...)` helper instead of calling
  `asyncio.run(...)` directly in Ternforge-managed Python libraries.
- Organize workbench files in project-appropriate subfolders; prefer related scripts together instead of one large flat directory.
- Keep workbench subfolders narrow: group one provider, seam, or hypothesis family together, and avoid cross-folder helper sharing that couples unrelated probes.
- Keep workbench scripts live-first.
- Do not use mocks, fakes, local scripted servers, snapshots, or workbench-only CLIs in `workbench/`.
- Use real repo fixtures or real local data when possible instead of artificial workbench-only inputs.
- Workbench scripts are manual-only and must not be part of default commit hooks or default CI paths.

## Rules

- Keep the top-level section order fixed.
- Write docstring `Checks` lines in explicit `If <condition>, then <consequence>.`
  form so the proving condition and expected observed result stay obvious.
- Make docstring `Checks` cover every meaningful validated field, derived flag,
  or observed success condition the script uses as manual proof.
- Start each executable workbench script with a top-of-file `# %%` marker so
  the file works cleanly in IDE cell-based execution, matching the e2e layout.
- If a script keeps the `Helpers` section for layout consistency but has no
  local helpers, use `# No local helpers for this scenario.`
- Group-specific helpers can live alongside related scripts when that keeps the
  layout clear.
- If the real output fits within 12 lines and 800 characters, show it in full.
- If it is larger, show a representative excerpt and say that it was cut.
- If the output cannot be represented directly, describe the expected visible
  result instead.

## Section Notes

`Scenario` should make the real setup easy to trust. Keep the fixed prompt,
fixture, model, endpoint, or dependency choice close to the reason it was
chosen.

`Helpers`, `Pipeline`, and `Demo (Manual Execution)` should read like a short
walkthrough when the behavior is not obvious. A reader should be able to follow
what the script is probing, why it takes each step, and what visible outcome
counts as success without reverse-engineering the whole file.

Use short comments where they add real guidance:

- why the script uses this prompt, fixture, or model
- why a helper extracts one field or response shape
- why a guard raises when a seam is missing
- why the observed output is enough to trust the behavior

`Demo (Manual Execution)` should narrate the same story the code is proving.
It should show what is about to happen, what was observed, and why that result
matters.

## Template

```python
# %%
"""Workbench scenario: one isolated behavior.

Why:
    Explain the dependency question this file proves.

Covers:
    Area: feature or dependency surface area
    Behavior: exact seam or behavior being checked
    Interface: concrete call, object path, or internal flow

Checks:
    If <condition>, then <expected behavior>.
    If <condition>, then <expected behavior>.

Examples:
    Run manually:
        uv run python -m workbench.group.example_script
        uv run python scripts/reproduce_running_loop.py workbench.group.example_script
"""

from __future__ import annotations

import json
from typing import Any

from py_lib_testkit import console


# =============================================================================
# Scenario
# =============================================================================

# Fixed inputs for the isolated behavior under test.
# Keep the setup close to the reason it was chosen.
# Explain why this model, fixture, prompt, or endpoint is fixed for the probe.


# =============================================================================
# Helpers
# =============================================================================


def _format_json(value: dict[str, Any]) -> str:
    """Format script evidence for readable console output."""
    return json.dumps(value, indent=2, sort_keys=True)


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline() -> dict[str, Any]:
    """Run the real behavior under test."""
    # This should read like the real dependency flow the script is inspecting,
    # not like scattered setup details.
    # Add short comments when a setup or extraction step would otherwise be
    # ambiguous to a reader running the file manually.
    return {"shape": "value"}


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the workbench script as a narrative manual demo."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Explain what real behavior is about to run.",
    )

    evidence = run_pipeline()
    console.demo_step(
        "Observed Seam",
        "Explain what the script returned or exposed.",
    )
    console.print(_format_json(evidence))
    console.demo_outcome(
        "Explain why the observed result counts as success for this behavior.",
    )


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run on 2026-03-20:
{
  "shape": "value"
}
""".strip()
```

Very short walkthrough-style illustration:

```python
def run_pipeline() -> dict[str, Any]:
    # First run the one real live call the script is about.
    response = live_client.do_one_call(_PROMPT)

    # Then extract only the seam we actually want to inspect manually.
    tool_call = response.items[0].tool_call
    if tool_call is None:
        msg = "The live response did not expose the expected tool call."
        raise RuntimeError(msg)

    return {"tool_name": tool_call.name}


def main() -> None:
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Running one live request with a single declared tool.",
    )

    result = run_pipeline()
    console.demo_step(
        "Observed Tool Call",
        "The live response exposed the exact protocol seam this script checks.",
        details=(f"tool_name: {result['tool_name']}",),
    )
    console.print_json(result)
    console.demo_outcome(
        "This is enough to trust that the provider returned a real tool call.",
    )
```
