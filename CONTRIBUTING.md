# Contributing to PortBoard

Thanks for helping improve PortBoard. Bug reports, focused feature proposals,
documentation fixes, and code contributions are welcome.

## Development setup

PortBoard requires Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/LeonPure/portboard.git
cd portboard
uv sync --locked
```

Run the dashboard or inspect its JSON output:

```bash
uv run portboard
uv run portboard --json
```

## Before opening a pull request

Run the same checks as CI:

```bash
uv run ruff check .
uv run mypy
uv run pytest
uv build --no-sources
```

Keep changes focused, add regression coverage for behavior changes, and follow
the dependency rules in [docs/architecture.md](./docs/architecture.md). Use
Conventional Commits with an imperative subject under 72 characters.

## Branch and review workflow

PortBoard uses two protected long-lived branches:

- `develop` is the default integration branch. Fork the repository, create a
  focused topic branch, and open contributions against `develop`.
- `main` is the release branch. It only receives owner-approved release pull
  requests from `develop` after a coherent set of changes is ready to publish.

All pull requests require passing CI and approval from the repository owner.
Only the owner can merge changes. Do not open feature pull requests directly
against `main`.

Releases are intentionally manual. The owner selects a release point, updates
the version and changelog on `develop`, merges `develop` into `main` through a
release pull request, and creates the matching protected `v*` tag. Only commits
already contained in `main` can be published to PyPI.

## Safety and compatibility

- Treat the JSON schema as a versioned public contract.
- Preserve partial results when optional integrations or metadata are unavailable.
- Keep process termination behind explicit confirmation and identity revalidation.
- Call out macOS- or Linux-specific behavior in the pull request.

Please report security vulnerabilities privately as described in
[SECURITY.md](./SECURITY.md), not in a public issue.
