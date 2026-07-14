# Isolated template lab architecture

## Scope and trust boundary

The pilot exists only in `betabitplus-template-lab`. The frozen legacy source is
`betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99` and is
cloned read-only. Every write-capable controller validates an explicit repository
allowlist before doing work.

The dependency direction is strictly one-way:

```text
components commit SHA
        ↓ Git submodule gitlink
final Copier template tag
        ↓ copier update
sandbox downstream
```

Components never depend on final templates. Templates never mutate components.
Downstreams never publish changes back to templates.

## Repositories

- `components`: frozen component payloads without the legacy assembler.
- `python-lib`: final template for `python-lib-standard`.
- `python-internal-package`: final template for the inherited internal profile.
- `python-starter-platform`: final platform template.
- `sandbox-python-lib`: one root Copier relationship.
- `sandbox-python-platform`: private platform relationship.
- `sandbox-workspace`: two nested Copier relationships.
- `lab-control`: Renovate, acceptance tests, release controller, and reports.

## Template composition

Each final template has `_subdirectory: template`, a standard
`.copier-answers.yml`, a hidden fixed `template_profile`, and a private Git
submodule at `template/_components` pinned by exact SHA.

The wiring rules are intentionally mechanical:

1. Ordinary text and binary files use file symlinks into `_components`.
2. Executable files use Jinja include wrappers stored with executable mode,
   because Copier dereferences a file symlink but does not preserve its mode.
3. `.gitignore` uses a wrapper to avoid Git's ignored-symlink edge cases.
4. A directory symlink is allowed only when its resolved target remains inside
   the template tree.
5. Jinja include paths are rooted at the cloned repository, so an include below
   `_subdirectory: template` uses `template/_components/...`.
6. `_components` and `_components/**` are excluded from output but remain
   available to the Jinja loader.

`WIRING.json` records component ownership, source path, SHA-256, mode, and wiring
type for every component-owned output file.

## Version boundary

Component commits are private implementation details. A downstream update is
made available only by a final-template Git tag. Tags are created by an
exact-SHA release controller which refuses to tag a commit that is no longer
`origin/main` and never moves an existing tag.

## Update automation

Template repositories enable only Renovate's `git-submodules` manager.
Downstreams enable only Renovate's `copier` manager. Global Renovate execution
uses an explicit request file, an immutable repository allowlist, no
autodiscovery, no onboarding, no automerge, and `allowScripts: false`.

The initial Copier templates contain no `_tasks` and no script migrations.
Validation belongs to CI rather than template execution.

## CI layers

- Template CI renders a sample and validates wiring, exclusion, conflict markers,
  and executable output on Linux, macOS, and Windows.
- The parity suite compares default and custom-answer candidate output against
  the frozen legacy build, allowing only documented migration differences.
- The Copier matrix exercises update, merge, conflict, add/delete/rename, mode,
  questions, `_skip_if_exists`, and nested relationships.
- Downstream CI rejects conflict markers and invalid/missing answers files.
- `lab-control` records machine-readable evidence for every controller run.

## Deliberately excluded legacy machinery

The pilot does not contain the manifest inheritance engine, component assembler,
committed build drift checker, custom Copier renderer, downstream registry,
fleet sync engine, or managed-repository onboarding workflow. The legacy
manifests and builds are used only to establish the frozen baseline.
