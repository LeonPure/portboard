## Summary

Describe the problem and the focused change that solves it.

## Target branch

- [ ] This is a feature or fix PR targeting `develop`.
- [ ] This is an owner-created release PR from `develop` to `main`.

Feature and fix PRs opened directly against `main` will fail the release-source policy.

## Validation

- [ ] `uv run ruff check .`
- [ ] `uv run mypy`
- [ ] `uv run pytest`
- [ ] `uv build --no-sources`
- [ ] Tests cover behavior changes.
- [ ] Platform-specific and JSON-contract impacts are documented.
