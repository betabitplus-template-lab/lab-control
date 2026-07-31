"""Shared Markdown parsing and validation helpers."""

from __future__ import annotations

import re
from pathlib import Path

from _shared.context import ErrorSink, ProjectContext
from _shared.reporting import expect

FILE_DESCRIPTION_VERBS = ("Explains ", "Defines ", "Shows ", "Indexes ")
INDEX_OVERVIEW_PARAGRAPHS = 1
MIN_FILE_DESCRIPTION_LINES = 2
NUMBERED_SECTION_INLINE_LABELS = (
    "Walkthrough:",
    "Why this is sufficient:",
    "Would fail if:",
    "Trust assumptions:",
    "Does not prove:",
)


def top_level_headings(text: str) -> list[str]:
    """Return all level-two Markdown headings."""
    return re.findall(r"^## (.+)$", text, flags=re.MULTILINE)


def heading_count(text: str, pattern: str) -> int:
    """Count heading-like matches in one Markdown file."""
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def section_body(text: str, heading: str) -> str | None:
    """Return the body of one level-two heading."""
    match = re.search(
        rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        return None
    return match.group(1).strip()


def first_nonempty_line(text: str) -> str:
    """Return the first non-empty line from one text block."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def nonempty_lines(text: str) -> list[str]:
    """Return all non-empty stripped lines from one text block."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def paragraphs(text: str) -> list[str]:
    """Return paragraph blocks from one text block."""
    return [
        block.strip() for block in re.split(r"\n\s*\n", text.strip()) if block.strip()
    ]


def numbered_headings(text: str) -> list[str]:
    """Return all numbered level-two heading titles."""
    return re.findall(r"^## \d+\. (.+)$", text, flags=re.MULTILINE)


def numbered_sections(text: str) -> list[tuple[str, str]]:
    """Return numbered level-two heading titles paired with their bodies."""
    matches = list(re.finditer(r"^## \d+\. (.+)$", text, flags=re.MULTILINE))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group(1), text[start:end].strip()))
    return sections


def subsection_body(text: str, heading: str) -> str | None:
    """Return the body of one level-three heading inside a text block."""
    match = re.search(
        rf"^### {re.escape(heading)}\n(.*?)(?=^### |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        return None
    return match.group(1).strip()


def indented_bullet_descriptions(text: str) -> list[str]:
    """Return joined indented descriptions for bullet entries."""
    lines = text.splitlines()
    descriptions: list[str] = []
    index = 0
    while index < len(lines):
        if not lines[index].startswith("- "):
            index += 1
            continue
        description_lines: list[str] = []
        index += 1
        while index < len(lines):
            line = lines[index]
            if not line.strip():
                index += 1
                continue
            if line.startswith("- "):
                break
            if line.startswith("  "):
                description_lines.append(line.strip())
                index += 1
                continue
            break
        descriptions.append(" ".join(description_lines))
    return descriptions


def require_overview_start(
    context: ProjectContext,
    path: Path,
    text: str,
    errors: ErrorSink,
) -> None:
    """Require the expected opening sentence for one overview."""
    overview = section_body(text, "Overview")
    expect(context, path, overview is not None, "missing `Overview` section", errors)
    if overview is None:
        return

    first_line = first_nonempty_line(overview)
    display_path = context.display_path(path).replace("\\", "/")
    if path.name == "README.md":
        expect(
            context,
            path,
            first_line.startswith("These docs describe "),
            "overview should start with `These docs describe`",
            errors,
        )
        return
    if path.name == "usage.md":
        expect(
            context,
            path,
            first_line.startswith("This document shows "),
            "overview should start with `This document shows`",
            errors,
        )
        return
    if "/architecture/principles/" in display_path:
        expect(
            context,
            path,
            first_line.startswith("This document defines "),
            "overview should start with `This document defines`",
            errors,
        )
        return

    expect(
        context,
        path,
        first_line.startswith("This document describes "),
        "overview should start with `This document describes`",
        errors,
    )


def require_index_overview_shape(
    context: ProjectContext,
    path: Path,
    text: str,
    errors: ErrorSink,
) -> None:
    """Require index overviews to use one stable single-paragraph pattern."""
    overview = section_body(text, "Overview")
    expect(context, path, overview is not None, "missing `Overview` section", errors)
    if overview is None:
        return

    blocks = paragraphs(overview)
    expect(
        context,
        path,
        len(blocks) == INDEX_OVERVIEW_PARAGRAPHS,
        "index `Overview` should contain exactly one short paragraph",
        errors,
    )


def require_diagram_question_and_mermaid(
    context: ProjectContext,
    path: Path,
    text: str,
    errors: ErrorSink,
    *,
    required: bool = True,
) -> None:
    """Require paired diagram-question lines and Mermaid blocks."""
    question_matches = list(
        re.finditer(
            r"^Question this diagram answers: .+$",
            text,
            flags=re.MULTILINE,
        )
    )
    diagram_matches = list(re.finditer(r"^```mermaid\s*$", text, flags=re.MULTILINE))
    if not required and not question_matches and not diagram_matches:
        return

    expect(
        context,
        path,
        bool(question_matches),
        "missing `Question this diagram answers:` line",
        errors,
    )
    expect(
        context,
        path,
        bool(diagram_matches),
        "missing Mermaid diagram block",
        errors,
    )
    if not question_matches or not diagram_matches:
        return

    expect(
        context,
        path,
        len(question_matches) == len(diagram_matches),
        "each Mermaid diagram should have one matching question line",
        errors,
    )
    for question_match, diagram_match in zip(
        question_matches,
        diagram_matches,
        strict=True,
    ):
        expect(
            context,
            path,
            question_match.start() < diagram_match.start(),
            "diagram question should appear before the Mermaid block",
            errors,
        )


def require_no_diagram(
    context: ProjectContext,
    path: Path,
    text: str,
    errors: ErrorSink,
) -> None:
    """Require one doc to omit question-line and Mermaid-diagram scaffolding."""
    expect(
        context,
        path,
        "Question this diagram answers:" not in text,
        "doc should not include a diagram question line",
        errors,
    )
    expect(
        context,
        path,
        "```mermaid" not in text,
        "doc should not include a Mermaid diagram",
        errors,
    )


def require_index_descriptions(
    context: ProjectContext,
    path: Path,
    text: str,
    errors: ErrorSink,
) -> None:
    """Require stable WHAT/WHY descriptions under `Files`."""
    files = section_body(text, "Files")
    expect(context, path, files is not None, "missing `Files` section", errors)
    if files is None:
        return

    lines = files.splitlines()
    bullet_indexes = [
        index for index, line in enumerate(lines) if line.startswith("- [")
    ]
    expect(
        context,
        path,
        bool(bullet_indexes),
        "`Files` should contain markdown links",
        errors,
    )
    for index in bullet_indexes:
        description_lines: list[str] = []
        cursor = index + 1
        while cursor < len(lines):
            line = lines[cursor]
            if not line.strip():
                cursor += 1
                continue
            if line.startswith("- ["):
                break
            if line.startswith("  "):
                description_lines.append(line.strip())
                cursor += 1
                continue
            break
        description = " ".join(description_lines)
        expect(
            context,
            path,
            bool(description),
            "each file entry should have indented `WHAT` and `WHY` lines",
            errors,
        )
        if description:
            expect(
                context,
                path,
                description.startswith(FILE_DESCRIPTION_VERBS),
                (
                    "file descriptions should start with `Explains`, "
                    "`Defines`, `Shows`, or `Indexes`"
                ),
                errors,
            )
        expect(
            context,
            path,
            len(description_lines) >= MIN_FILE_DESCRIPTION_LINES,
            "each file entry should use two indented lines: `WHAT` then `WHY`",
            errors,
        )
        if len(description_lines) >= MIN_FILE_DESCRIPTION_LINES:
            expect(
                context,
                path,
                description_lines[1].startswith("Use it to "),
                "the second file-description line should start with `Use it to `",
                errors,
            )


def require_heading_order(
    context: ProjectContext,
    path: Path,
    headings: list[str],
    required: list[str],
    errors: ErrorSink,
) -> None:
    """Require a stable relative heading order."""
    last_index = -1
    for heading in required:
        expect(
            context,
            path,
            heading in headings,
            f"missing `{heading}` section",
            errors,
        )
        if heading not in headings:
            continue
        current_index = headings.index(heading)
        expect(
            context,
            path,
            current_index > last_index,
            f"`{heading}` is out of order",
            errors,
        )
        last_index = current_index


def require_section_subheadings(
    context: ProjectContext,
    path: Path,
    text: str,
    section_heading: str,
    errors: ErrorSink,
) -> None:
    """Require one level-two section to contain level-three subheadings."""
    body = section_body(text, section_heading)
    expect(
        context,
        path,
        body is not None,
        f"missing `{section_heading}` section",
        errors,
    )
    if body is None:
        return
    count = len(re.findall(r"^### .+$", body, flags=re.MULTILINE))
    expect(
        context,
        path,
        count >= 1,
        f"`{section_heading}` should contain at least one `###` subsection heading",
        errors,
    )


def require_numbered_heading_prefix(
    context: ProjectContext,
    path: Path,
    text: str,
    prefix: str,
    errors: ErrorSink,
) -> None:
    """Require all numbered level-two headings to share one title prefix."""
    for heading in numbered_headings(text):
        expect(
            context,
            path,
            heading.startswith(prefix),
            f"numbered headings should start with `{prefix}`",
            errors,
        )


def require_numbered_section_line_prefix(
    context: ProjectContext,
    path: Path,
    text: str,
    rule: tuple[int, str],
    errors: ErrorSink,
) -> None:
    """Require one numbered section line to share one stable prefix."""
    line_index, prefix = rule
    for _, body in numbered_sections(text):
        lines = nonempty_lines(body)
        expect(
            context,
            path,
            len(lines) > line_index,
            "numbered section should include the expected intro lines",
            errors,
        )
        if len(lines) <= line_index:
            continue
        expect(
            context,
            path,
            lines[line_index].startswith(prefix),
            f"numbered section line {line_index + 1} should start with `{prefix}`",
            errors,
        )


def require_numbered_subsection_bullet_description_prefix(
    context: ProjectContext,
    path: Path,
    text: str,
    rule: tuple[str, str],
    errors: ErrorSink,
) -> None:
    """Require numbered-section evidence bullets to share one description prefix."""
    subsection_heading, prefix = rule
    for _, body in numbered_sections(text):
        subsection = subsection_body(body, subsection_heading)
        expect(
            context,
            path,
            subsection is not None,
            f"numbered section should include `### {subsection_heading}`",
            errors,
        )
        if subsection is None:
            continue
        descriptions = indented_bullet_descriptions(subsection)
        expect(
            context,
            path,
            bool(descriptions),
            f"`### {subsection_heading}` should contain described bullets",
            errors,
        )
        for description in descriptions:
            expect(
                context,
                path,
                description.startswith(prefix),
                (
                    f"`### {subsection_heading}` bullet descriptions should start with "
                    f"`{prefix}`"
                ),
                errors,
            )


def require_numbered_subsection_line_prefix(
    context: ProjectContext,
    path: Path,
    text: str,
    rule: tuple[str, int, str],
    errors: ErrorSink,
) -> None:
    """Require one numbered-section subsection line to share one stable prefix."""
    subsection_heading, line_index, prefix = rule
    for _, body in numbered_sections(text):
        subsection = subsection_body(body, subsection_heading)
        expect(
            context,
            path,
            subsection is not None,
            f"numbered section should include `{subsection_heading}:`",
            errors,
        )
        if subsection is None:
            continue
        lines = nonempty_lines(subsection)
        expect(
            context,
            path,
            len(lines) > line_index,
            (f"`{subsection_heading}:` should include the expected non-empty lines"),
            errors,
        )
        if len(lines) <= line_index:
            continue
        expect(
            context,
            path,
            lines[line_index].startswith(prefix),
            (
                f"`{subsection_heading}:` line {line_index + 1} should start "
                f"with `{prefix}`"
            ),
            errors,
        )


def require_numbered_subsection_description_prefix(
    context: ProjectContext,
    path: Path,
    text: str,
    rule: tuple[str, str],
    errors: ErrorSink,
) -> None:
    """Require one subsection to reach a stable description after link lines."""
    subsection_heading, prefix = rule
    for _, body in numbered_sections(text):
        subsection = subsection_body(body, subsection_heading)
        expect(
            context,
            path,
            subsection is not None,
            f"numbered section should include `### {subsection_heading}`",
            errors,
        )
        if subsection is None:
            continue
        lines = nonempty_lines(subsection)
        description = next(
            (
                line
                for line in lines
                if not line.startswith("[") and not line.startswith("```")
            ),
            None,
        )
        expect(
            context,
            path,
            description is not None,
            f"`### {subsection_heading}` should contain a description line",
            errors,
        )
        if description is None:
            continue
        expect(
            context,
            path,
            description.startswith(prefix),
            (
                f"`### {subsection_heading}` description lines should start "
                f"with `{prefix}`"
            ),
            errors,
        )


def require_numbered_labeled_block_line_prefix(
    context: ProjectContext,
    path: Path,
    text: str,
    rule: tuple[str, int, str],
    errors: ErrorSink,
) -> None:
    """Require one inline labeled block in each numbered section."""
    label, line_index, prefix = rule
    label_line = f"{label}:"
    stop_lines = set(NUMBERED_SECTION_INLINE_LABELS)
    for _, body in numbered_sections(text):
        lines = body.splitlines()
        block_lines: list[str] | None = None
        for index, line in enumerate(lines):
            if line.strip() != label_line:
                continue
            collected: list[str] = []
            cursor = index + 1
            while cursor < len(lines):
                current = lines[cursor]
                stripped = current.strip()
                if stripped in stop_lines:
                    break
                collected.append(current)
                cursor += 1
            block_lines = nonempty_lines("\n".join(collected))
            break

        expect(
            context,
            path,
            block_lines is not None,
            f"numbered section should include `{label}:`",
            errors,
        )
        if block_lines is None:
            continue
        expect(
            context,
            path,
            len(block_lines) > line_index,
            f"`{label}:` should include the expected non-empty lines",
            errors,
        )
        if len(block_lines) <= line_index:
            continue
        expect(
            context,
            path,
            block_lines[line_index].startswith(prefix),
            f"`{label}:` line {line_index + 1} should start with `{prefix}`",
            errors,
        )
