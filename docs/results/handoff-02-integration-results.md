# Handoff-02 integration results

Date: 2026-07-15  
Source bundle SHA-256: `5894d7468d2a5473e44c649fccebbff139c79f391b044014992de495b1ef18d6`  
Source branch at execution: `lab-control@a97f42cf351a57e824001876b8d2d3bdbc8f5fe2`

## Decision

**CONDITIONAL GO remains the correct architecture decision.**

Handoff-02 substantially strengthened the evidence. The architecture itself worked in live private repositories: private reusable workflows, Renovate private presets and topic discovery, reviewed live Renovate PR creation and idempotency, the `dev → main` repository shape, Release Please v0.4.0/v0.4.1, nested lock regeneration, component wiring edges, private-access failure/success and direct-tool parity were exercised.

The run also found ten genuine failures in the prepared implementation/fixtures and five blocked items. Those failures are preserved in [`handoff-02-report.json`](../evidence/handoff-02-report.json); they are not rewritten into passes. The implementation defects have been corrected in reviewable lab branches and now require the bounded handoff-03 revalidation. Three ruleset/tag-protection checks remain blocked by the current GitHub plan.

## Immutable source result

| Status | Count |
|---|---:|
| PASS | 40 |
| NEGATIVE_PASS | 6 |
| FAIL | 10 |
| BLOCKED | 5 |

Safety results:

- production mutations: **0**;
- automerge enabled: **false**;
- `sandbox-python-lib#3` merged: **false**;
- temporary credentials revoked: **yes**;
- credential findings: **0**.

## Important live passes

### Private reusable workflows

- `automation` was created private and published at `a5cd8112c8e8b221dceb397c1e882a9a25148b86`, tag `v0.1.0`.
- Organization access for private callers was enabled.
- Linux/macOS and inherited-secret/read-only permission run: `29375576270`.
- Intentional failure propagated: `29375625874`.
- Cancellation propagated: `29375658789`.
- Tagged ref worked: `29375727768`.
- Final exact-SHA caller worked: `29375763651`.
- Caller remains `sandbox-python-platform#3`; automerge is off.

### Renovate

- Private presets were published and consumed.
- Explicit allowlist `extract`, `lookup` and `full` dry phases passed.
- Organization/topic discovery included the expected managed/template/downstream/workspace/untagged fixtures and excluded the disabled fixture.
- One reviewed live run created expected PRs; rerun created no duplicates.
- All observed Renovate PRs had `auto_merge=null`.

### Process and releases

- `sandbox-process` was created with `dev` as default and a `main` baseline.
- A safe update PR passed CI and merged to `dev`: `sandbox-process#1`, run `29376918751`.
- Exactly one promotion PR remained open: `sandbox-process#2`.
- Release Please produced `python-lib` v0.4.0 and v0.4.1.
- v0.4.0 tag/release/main target: `0477653722f8a8b125e2bd3963b37d4a0d10c153`, release `354133543`.
- v0.4.1 tag/release/main target: `1a4fabe2c0449c5fe92d745eea0f9494c6fed160`, release `354137656`.
- Old v0.1.0-v0.3.0 tags were not rewritten.

### Locks, wiring, access and tooling

- Exact `uv.lock` baseline and CI passed in `sandbox-process#3`, run `29377905812`.
- Both nested workspace locks regenerated idempotently with private Git authentication.
- New-file/no-implicit-output, explicit wiring, broken-symlink negative and rename cases were exercised.
- Wiring audit counted 165 symlinks and zero broken links in the positive final state.
- A credential without components read failed recursive clone; adding components read succeeded; temporary credentials were revoked.
- Legacy/direct quality rule parity was 8/8; residual policy rule parity was 12/12.
- Wheel and sdist build, metadata checks and isolated installs passed.

## Failure remediation

| Handoff IDs | Root cause | Correction | Review location |
|---|---|---|---|
| S03, D05 | malformed shell heredoc; packaging tools assumed to be in project env; Copier answers filename not ignored | removed heredoc, used pinned `uvx` tools, exact `.copier-answers.yml` ignore | `lab-control#9`, commit `0a28b2f3` |
| S04, R03, T01, T03 | provider 6.6.0 does not expose `allowed_merge_methods` in repository rulesets | removed unsupported argument; squash-only remains enforced by repository merge settings | `lab-control#9`, commit `7f241a8d` |
| P04 | `persist-credentials:false` followed by unauthenticated `git fetch` | promotion controller now uses authenticated GitHub compare/PR APIs and no checkout | `lab-control#9`, commit `d8ad5ad9` |
| L04 | Copier's independent temporary clone lacked private components authentication | ephemeral Git URL rewrite from the masked read token on Linux/macOS/Windows; no credential persistence | `lab-control#9`, commits `51dcb45c`, `0bf9ee3f` |
| D03 | policy rejected generated version fallback and example package `__init__.py` | corrected `try/except` traversal; exempted initializer; expanded to eight tests | `lab-control#9`, commits `25f78794`, `7113f926` |
| K06 | Renovate did not extract PEP 508 Git tags through `pep621` | added constrained `custom.regex` manager for only `py-lib-runtime`/`py-lib-tooling`, GitHub tags and semver, retaining exact `uv lock` task | `lab-control#9`, commit `8d055e49` |
| K03 | pre-profile downstream answers omitted hidden `template_profile` | `_skip_if_exists` now uses the hidden question's existing default when old answers omit it | `python-lib#19`, head `fb701f47` |
| K05 | nested fixture hardcoded `v0.2.0` | requires both exact answer paths, valid semver tags and one shared version instead of a historical constant | `sandbox-workspace#8`, head `ba4eedbb` |

## Still blocked by external capability

The following are not implementation failures and remain `BLOCKED`:

- P06: private branch rulesets/protections;
- T04: OpenTofu ruleset phase;
- L05: immutable private release-tag ruleset.

Every attempted private ruleset endpoint returned GitHub's plan-related HTTP 403. Production rollout therefore requires either a plan with private rulesets or a separately approved, explicitly lower-fidelity branch-protection fallback. The experiment does not silently substitute the fallback.

## Required revalidation

Handoff-03 is intentionally limited to the remediated failures. Previously passing live phases must not be repeated unless required as a dependency. It must prove:

1. actionlint and packaging-chain success after S03/D05 fixes;
2. OpenTofu validate, repository-only apply, bootstrap, post-bootstrap apply and no-drift after S04/T01 fix;
3. promotion workflow success/idempotency after P04 fix;
4. private Copier acceptance and Release Please workflow after L04 fix;
5. real old-answers Copier update plus `uv lock` through `python-lib#19`;
6. nested workspace CI through `sandbox-workspace#8`;
7. normal Renovate PR extraction for PEP 508 `py-lib-runtime`/`py-lib-tooling`;
8. minimal policy success on the real generated baseline and exact packaging-chain success.

## Safety conclusion

Handoff-02 made only lab mutations. Production repositories and the frozen production baseline remained unchanged. No production migration has started. The draft status of `lab-control#9` and the two remediation PRs is intentional until handoff-03 evidence is integrated.
