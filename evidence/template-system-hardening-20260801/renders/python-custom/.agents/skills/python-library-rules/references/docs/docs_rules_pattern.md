---
name: docs-rules-pattern
description: Reusable project documentation rules and preferences. Use when you need one grouped rules reference before shaping or reviewing project docs.
---

# Documentation Rules

## Overview

Use this guide for general project documentation rules and preferences.

## When To Use

Use this guide when creating, reorganizing, or reviewing project docs.

Use this guide when the goal is short, structured documentation that explains
stable concepts clearly, or explicitly proves how one stable claim is realized
in current implementation.

## Core Rules

### Scope Rules

- Keep docs short, structured, and high-signal.
- One doc should own one concern.
- Prefer stable requirements, logic, data flow, dependency flow, and public
  behavior over implementation detail.
- For architecture docs, explain how the system holds together, not how the
  current files are arranged.
- Avoid private module references, internal paths, and implementation-specific
  mechanics unless the doc explicitly requires them.
- Do not duplicate the same explanation across multiple docs.

### Selection Rules

- Follow `docs_organization_pattern.md` when the main question is docs-tree
  shape, folder boundaries, or architecture-doc grouping.
- Use the narrowest matching template for an individual doc file.
- Let the matching template own exact section order, repeated heading names,
  and local grammar such as example, proof, or index-entry scaffolding.

### Shared Writing Rules

- Keep `Overview` short:
  one short paragraph for index docs, and one or two short paragraphs for most
  other doc families.
- Keep sibling bullets grammatically parallel instead of mixing noun phrases,
  commands, and fragments.
- Write `Rules` as imperative or directive statements.
- Use `Invariants` only when they add durable meaning that is not already
  captured by nearby prose or `Rules`.
- When `Invariants` are present, write them as declarative statements about
  what remains true.
- Use one sentence starting with `Red flag:` only for a concrete failure mode
  or semantic trap that adds new information instead of restating a rule.
- For doc families without a dedicated `Invariants` section, fold durable
  truths into the relevant model, flow, strategy, or `Rules` sections instead
  of ending with a summary recap.
- Keep most non-overview sections to one short opener plus one flat list or a
  few approved `###` subsections.
- Keep list lengths narrow and predictable; prefer roughly 3-5 bullets per
  short section, and avoid going past 6 unless the list is intentionally
  exhaustive.

### Frontmatter Rules

- Use only `name`, `doc_type`, and `description`.
- Keep `description` in the same style as skill metadata:
  what the doc is, and when to use it.
- Do not add extra frontmatter unless tooling actually uses it.

### Linking Rules

- Add inline links only when the current sentence benefits from them.
- Use index docs for navigation and architecture docs for explanation.
- Do not add generic `Related Docs` or catalog-style end sections.
- Prefer links between docs that clarify the reader's next step.
- Prefer one short bridge phrase such as `See [...] for details.` instead of
  rotating between many near-synonyms for cross-doc references.

### Diagram Rules

- Add a question line before any diagram.
- Where a doc family uses diagrams, keep each Mermaid diagram paired with one
  diagram-question line.
- Do not use diagrams in index docs or principles docs.
- Use a diagram only when it clarifies the concept better than prose.
- Prefer the Mermaid type that best matches the concept:
  `flowchart` for broad structure,
  `sequenceDiagram` for ordered participation,
  `stateDiagram-v2` for state changes,
  `classDiagram` for public data shapes.
- Prefer one default Mermaid choice per doc family unless a different one is
  clearly better:
  `flowchart LR` for top-level system docs,
  `sequenceDiagram` for lifecycle or flow docs,
  `stateDiagram-v2` for stateful or continuity docs,
  `classDiagram` for public model docs,
  `flowchart TD` for verification docs,
  and no diagram by default for principles or index docs.

### Table Rules

- Use tables only when the tabular form is genuinely better than a flat list.
- Keep tables narrow.
- Prefer 3 columns, and avoid more than 4.
- Do not use tables to restate nearby prose.

### Callout Rules

- Use callouts only for real boundaries, caveats, or semantic traps.
- Do not use callouts as decoration.
- If the same point fits naturally inside nearby prose or `Rules`, prefer that
  over a callout.

## Validation

- Use the bundled CLI checker when a docs tree follows this architecture,
  verification, and usage shape:
  `scripts/check_docs_shape.py <docs-root> [--repo-root <repo-root>]`.
- Use the checker for repeatable section-order, heading-grammar, and
  file-description validation rather than re-reviewing those mechanics by eye.
