# Template composition and delivery lab: final results

Date: 2026-07-14  
Organization: `betabitplus-template-lab`  
Frozen read-only source: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`

## Executive conclusion

The proposed architecture is viable.

The lab demonstrated an end-to-end private delivery chain:

1. shared component commit;
2. Renovate submodule PR in an independently versioned Copier template;
3. three-platform template acceptance;
4. exact-SHA annotated template release;
5. Renovate Copier PR in downstream repositories;
6. preservation of user-owned changes;
7. grouped nested relationship updates;
8. explicit conflict markers and red CI for a real overlapping edit;
9. one-line template rollback to a prior component SHA.

No write was made to any existing `betabitplus/*` repository. All mutations were restricted to the eight private lab repositories.

## Repository final state

| Repository | Final purpose/state |
|---|---|
| `components` | Shared components; `main` contains C3 `4e1cf398a5a9ddc0da2aeeb1cb8986968fea37d7` for the negative test. |
| `python-lib` | Standard library template; final `main` `2d3168df64f37b1ad5ab7128ea8f2dcd01fa0e9d`, rolled back to component C2 `5d6187b1cd3adec8499761cfa2302a72a6169dcd`. |
| `python-internal-package` | Internal-package template at v0.2 state, `main` `88f484f5f0dd7bcfd748585bcd5c13eb19f8b0a0`. |
| `python-starter-platform` | Platform template at v0.2 state, `main` `06bba8f30d0bf22a05b430861b8115e1e68b5304`. |
| `sandbox-python-lib` | Clean v0.2 update merged; deliberate local conflict baseline retained on `main` `0386f7a5bbdb52926a508bd1986d725e13e17913`. One expected-failure v0.3 PR remains open. |
| `sandbox-python-platform` | Clean v0.2 platform update merged as `7ff13343b611f5c4f196fd8be3b41c17dbf2c348`. |
| `sandbox-workspace` | Both nested relationships updated together and merged as `b4c1645c026eeb6eaa0a5d8ccc17883b7f67ffbd`. |
| `lab-control` | Guarded Renovate/release controllers, acceptance matrix, evidence, ADR and final report. |

## Acceptance matrix

| Requirement | Result | Evidence |
|---|---|---|
| Eight isolated private repositories | PASS | Repository audit; no production writes. |
| Frozen-source parity, defaults and custom answers | PASS | Preparation run `29340195367`; `docs/results/prepare.json`. |
| Composition behavior | PASS | Text/Jinja/binary/empty sources, loader root, internal directory symlink, wrapper mode and output exclusion recorded in `prepare.json`. |
| Copier update matrix on Linux and macOS | PASS | Run `29339334451`; `docs/results/copier-matrix.json`, failures `[]`. |
| Private recursive submodule checkout | PASS | Template CI on Linux, macOS and Windows. |
| Renovate guarded extract | PASS | Pinned Renovate `43.262.4`, exit `0`; no mutations during extract stage. |
| Component C2 affects multiple templates | PASS | C2 `5d6187b1...`; Renovate created one gitlink-only PR in each of three templates. |
| Template PR diff is only the gitlink | PASS | `python-lib#1`, `python-internal-package#1`, `python-starter-platform#1`. |
| Template CI cross-platform | PASS | C2 success runs: `29351347488`, `29351358339`, `29351371006`. |
| Exact-SHA v0.2 template release | PASS | Release run `29351624014`; annotated tags point to the requested `main` SHAs. |
| Root downstream Copier update | PASS | `sandbox-python-lib#2`, merged `f77e2fe0b8a455859d6214c29f9e72536c37d850`; lab validation `29352551580`. |
| Private platform downstream update | PASS | `sandbox-python-platform#1`, merged `7ff13343b611f5c4f196fd8be3b41c17dbf2c348`; lab validation `29352578597`. |
| Two nested answers files | PASS | `sandbox-workspace#1` grouped runtime and tooling; merged `b4c1645c...`; validation `29352212829`. |
| User-owned files and mixed changes preserved | PASS | Acceptance scripts verify marker files, domain modules, mixed pyproject edit and absence of conflict markers. |
| Rerun idempotency | PASS | Repeated Renovate runs reused/rebased existing PRs and produced no new PR after clean merges. |
| Real downstream conflict | EXPECTED FAIL / PASS | C3 component `4e1cf398...`, template tag `v0.3.0`, `sandbox-python-lib#3` contains conflict markers `96` versus `120`; lab CI `29353371296` is red. PR remains open and unmerged. |
| Rollback | PASS | `python-lib#4` changed only the gitlink from C3 to C2; rollback CI `29353504047` passed on Linux, macOS and Windows; merged as `2d3168df...`. |
| Production isolation | PASS | Controllers reject targets outside `betabitplus-template-lab/`; reported production mutations: `0`. |

## Version and commit chain

### Component chain

- C1: `1f233492f3f66fdf17096cdb9462e4d38a04e8fc`
- C2: `5d6187b1cd3adec8499761cfa2302a72a6169dcd`
  - `.editorconfig`: `max_line_length = 100`
  - shared identity README release statement
- C3: `4e1cf398a5a9ddc0da2aeeb1cb8986968fea37d7`
  - negative test: `.editorconfig` changes the same line to `120`

### Template v0.2 releases

- `python-lib@v0.2.0` → `c95e5dfda98677def34cc656aba9945b4e6eddd5`
- `python-internal-package@v0.2.0` → `88f484f5f0dd7bcfd748585bcd5c13eb19f8b0a0`
- `python-starter-platform@v0.2.0` → `06bba8f30d0bf22a05b430861b8115e1e68b5304`

### Negative-test release

- `python-lib@v0.3.0` → `8e0be803c19e50ee722eab8dc57222b576ecc87c`
- This tag remains immutable evidence even though `python-lib/main` was subsequently rolled back to C2.

## Clean downstream update results

### `sandbox-python-lib#2`

Expected changes occurred:

- answers `v0.1.0 → v0.2.0`;
- `.editorconfig` received C2;
- legacy `sync-starter-template.yml` was removed;
- `LAB_USER_OWNED.txt`, `src/sandbox_python_lib/domain.py` and the downstream pyproject note survived.

The generated production CI expected production App credentials and the `dev → main` policy. The isolated lab deliberately did not receive those credentials. Its workflow was retained as a manual diagnostic, while `Lab downstream validation` became the PR gate.

### `sandbox-python-platform#1`

- answers `v0.1.0 → v0.2.0`;
- `.editorconfig` received C2;
- platform-specific user-owned marker and domain module survived;
- lab validation passed.

### `sandbox-workspace#1`

One Renovate PR updated both:

- `packages/runtime/.copier-answers.yml`;
- `packages/tooling/.copier-answers.yml`.

Both package trees received C2 EditorConfig and README changes, and exactly two nested relationships remained present.

## Conflict experiment

After the clean v0.2 merge, `sandbox-python-lib/main` intentionally changed:

```text
max_line_length = 100
```

to:

```text
max_line_length = 96
```

C3 independently changed the same ancestral template line to `120`. Renovate's Copier update generated:

```text
<<<<<<< before updating
max_line_length = 96
=======
max_line_length = 120
>>>>>>> after updating
```

This proves conflicts are visible as ordinary PR content and CI failures, not silently overwritten. The PR is intentionally open and must not be merged.

## Rollback experiment

The rollback PR changed only:

```text
template/_components: 4e1cf398... → 5d6187b1...
```

No component rebuild or file-copy operation was required. The exact same template acceptance matrix passed on all three operating systems before merge.

## Important discoveries and deviations

1. Copier's loader root is the repository root even with `_subdirectory: template`; Jinja wrapper sources therefore use `template/_components/...`.
2. Executable file symlinks are dereferenced without preserving mode. Executable Jinja wrappers are required.
3. Windows checkout/render works, but POSIX executable-bit assertions must be skipped on Windows.
4. Canonical HTTPS `_src_path` values are required for Renovate Copier extraction in this configuration; `gh:` shorthand did not produce an update.
5. The isolated Renovate App has `Workflows: No access`. Four initial generated platform workflow files were published by the lab connector rather than expanding App permissions.
6. Profile overlays (`renovate.json5`) and intentionally removed legacy files must be explicit acceptance-policy entries.
7. Renovate's Dependency Dashboard issues remain open as operational observability. They are not failures.
8. An early obsolete diagnostic commit captured a short-lived lab installation token. It had lab-only scope and expired automatically; current logs redact tokens. Rotating the lab Renovate App key is still recommended as hygiene.

## Final open items by design

- `sandbox-python-lib#3`: open, red, expected conflict evidence.
- Renovate Dependency Dashboard issues in the sandbox repositories.

There are no other open pull requests in the lab organization at report time.

## Recommendation

Proceed with the composed-template architecture for production design, subject to the permission, branch-protection and workflow-publication decisions documented in ADR 0001. Keep the current lab organization as reproducible evidence until the production rollout is reviewed.

## Final production-shaped phase

The first-stage evidence above remains unchanged. The final platform-minimization phase is documented separately in:

- [`final-experiment-results.md`](final-experiment-results.md)
- [`replacement-matrix.md`](replacement-matrix.md)
- [`minimal-custom-surface.md`](minimal-custom-surface.md)
- [`production-gap-analysis.md`](production-gap-analysis.md)
- ADR 0002 and ADR 0003

The final phase concludes **CONDITIONAL GO**: the composed Copier/Renovate design is sound and removes the custom lifecycle engine, while production rollout remains conditional on organization-level private reusable-workflow access, ruleset-capable GitHub licensing, and live OpenTofu/Renovate acceptance runs with lab-only administrative credentials.
