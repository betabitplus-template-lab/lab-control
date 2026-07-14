# ADR 0001: Composed Copier templates with versioned private components

- Status: Accepted for the isolated lab
- Date: 2026-07-14
- Scope: `betabitplus-template-lab/*` only
- Frozen baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`

## Context

The legacy starter can build several generated profiles, but a production architecture also needs independently versioned reusable components, independently released templates, Renovate-driven delivery, safe downstream Copier updates, private-repository authentication, conflict visibility, and a simple rollback path.

The experiment was required to remain isolated from all existing `betabitplus/*` repositories and credentials.

## Decision

1. Keep three profile-specific Copier template repositories:
   - `python-lib`
   - `python-internal-package`
   - `python-starter-platform`
2. Put shared source components in the private `components` repository.
3. Mount `components` as the exact-SHA Git submodule `template/_components` in each template.
4. Use static file-level symlinks for non-executable component files.
5. Use executable Jinja wrappers for executable component files because Copier dereferences file symlinks without preserving their executable mode.
6. Keep `_components` inside the Copier loader tree but exclude it from generated output.
7. Treat the submodule gitlink as the sole component-version source of truth. `WIRING.json` records ownership, path, type and executable semantics, but not a duplicate component digest.
8. Use Renovate's `git-submodules` manager for component-to-template PRs.
9. Release templates with annotated tags created only after checking the requested commit equals the current `origin/main` SHA.
10. Use Renovate's Copier manager for template-to-downstream PRs. Answers files use canonical HTTPS Git URLs.
11. Keep Renovate autodiscovery and automerge disabled. Every controller run validates an explicit `betabitplus-template-lab/*` allowlist.
12. Use separate lab-only GitHub App credentials. No production repository access is required.

## Verified behavior

- Default and custom render parity passed for all three profiles against the frozen source baseline.
- Jinja includes resolve from the repository root, so wrapper sources use `template/_components/...`.
- Text, Jinja, binary, empty-file and internal directory symlinks render correctly.
- An internal directory symlink is valid only when its target resolves inside the template tree.
- File symlinks do not preserve executable mode; executable Jinja wrappers do.
- Private recursive submodule checkout works on Linux, macOS and Windows.
- Renovate updates only the gitlink for component changes and reuses existing PRs on reruns.
- Copier preserves unrelated user files and non-conflicting mixed edits, handles add/delete/rename and executable-bit changes, records new defaulted questions, and exposes real conflicts with markers.
- Two nested answers files can be grouped into one downstream PR and updated together.
- Rollback is a one-line gitlink change and passed the same three-platform template CI matrix.

## Authentication boundary

The isolated Renovate App has access only to the lab organization. `Workflows: Read-only` was unavailable in the GitHub App UI; `No access` was selected rather than granting write access. Consequently, initial publication of four generated platform workflows used the ChatGPT lab connector, while Renovate remained unable to mutate workflow files. This is safer for the experiment but must be resolved explicitly before production adoption if template updates are expected to change workflows.

Generated production CI in `sandbox-python-lib` expected the existing production automation App and a `dev -> main` policy. The lab did not receive those credentials. The workflow was retained as a manual diagnostic, and the lab-specific PR gate validated Copier state, user-owned files and conflict markers.

## Rejected alternatives

### Runtime manifest assembler

Rejected as the primary delivery mechanism. It adds an extra runtime composition layer, duplicates profile/build logic, and makes component ownership and exact source versions less visible in ordinary Git history.

### Copying component files into each template

Rejected because ownership becomes ambiguous and component updates create large duplicated diffs rather than one reviewable gitlink change.

### Executable file symlinks

Rejected because Copier dereferences them but does not preserve the executable bit.

### Floating submodule branches

Rejected because template rendering would cease to be reproducible. The `.gitmodules` branch hint may assist Renovate discovery, but the committed gitlink is always an exact SHA.

## Consequences

### Positive

- Small component update PRs.
- Exact, auditable component and template versions.
- Independent profile release cadence.
- Native Copier conflict behavior downstream.
- Simple rollback.
- No bespoke runtime assembler in the delivery path.

### Costs and limitations

- Template repositories contain many symlink entries and a generated ownership map.
- Windows cannot validate POSIX executable bits, so mode assertions run only on POSIX while Windows still validates checkout, source resolution and rendering.
- Canonical Git URLs are required for reliable Renovate Copier extraction; Copier's `gh:` shorthand was not detected in this run.
- Workflow-file changes require a credential with explicit Workflows permission or a separate trusted publisher.
- Profile overlays and intentionally removed legacy files must be declared in acceptance policy rather than treated as component drift.

## Production adoption recommendation

Adopt the architecture after:

1. defining a dedicated production GitHub App permission model, including an explicit decision for workflow mutations;
2. generating `WIRING.json` deterministically in template build/release tooling;
3. pinning controller actions and Renovate images by immutable digest where practical;
4. making template acceptance, exact-SHA release and downstream conflict checks required branch protections;
5. documenting profile overlays and removed legacy paths as first-class policy;
6. keeping a dry-run/extract stage before every live Renovate rollout.
