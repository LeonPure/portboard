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

## Safety and compatibility

- Treat the JSON schema as a versioned public contract.
- Preserve partial results when optional integrations or metadata are unavailable.
- Keep process termination behind explicit confirmation and identity revalidation.
- Call out macOS- or Linux-specific behavior in the pull request.

Please report security vulnerabilities privately as described in
[SECURITY.md](./SECURITY.md), not in a public issue.
