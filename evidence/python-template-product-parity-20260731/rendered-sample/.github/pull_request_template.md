# Summary

Describe the change in a few sentences.

## Scope

- [ ] `src/`
- [ ] `tests/`
- [ ] `docs/`
- [ ] `examples/`
- [ ] `workbench/`
- [ ] repository tooling, release, or CI

## Validation

- [ ] Ran `uv run pre-commit run --all-files`
- [ ] Ran `uv run pre-commit run --all-files --hook-stage pre-push`
- [ ] Ran targeted tests if behavior changed
- [ ] Ran affected `examples/` scripts if public API demos changed
- [ ] Ran affected `workbench/` scripts manually if probe logic changed

## Docs

- [ ] Docs not needed
- [ ] Updated user-facing docs
- [ ] Updated contributor or maintainer docs

## Notes

- Target branch is `dev` for normal development.
- If targeting `main` instead of `dev`, explain why.
- Mention actual validation outcome plus any follow-up work, caveats, or skipped validation here.
