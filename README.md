# PortBoard

> A terminal dashboard for discovering and managing local development services.

PortBoard aims to answer a deceptively simple question:

**What is running on my machine, and where can I access it?**

Modern development often means running a frontend, API, database, containers,
and several forgotten dev servers at the same time. PortBoard brings them into
one fast, readable terminal interface.

> [!NOTE]
> PortBoard is currently in the planning and early development stage.

## Current prototype

PortBoard has a live terminal dashboard with refresh, filtering, and sorting:

```bash
uv run portboard
```

The same discovery snapshot is also available as versioned JSON output for
scripts and bug reports:

```bash
uv run portboard --json
```

It reports visible TCP listeners together with best-effort process metadata and
their nearest Git project. When the operating system restricts access to a
process, the command preserves the remaining results and reports a warning.

## Planned experience

```text
┌ Project       Port    Status    Process       URL
│ my-blog       3000    healthy   node          http://localhost:3000
│ shop-api      8000    healthy   uvicorn       http://localhost:8000
│ postgres      5432    running   docker        localhost:5432
│ old-project   5173    unhealthy vite          http://localhost:5173
└
```

The first release is planned to:

- Discover listening ports and their processes automatically.
- Show the process, working directory, command, and Git repository.
- Detect HTTP services and check their health.
- Display Docker port mappings when Docker is available.
- Copy or open service URLs and stop unwanted processes.
- Provide a live terminal UI on macOS and Linux.

## Why PortBoard?

Existing commands can answer individual questions: `lsof` finds ports,
container tools list mappings, and process managers supervise declared apps.
PortBoard's goal is to provide a useful overview without requiring projects to
be configured in advance.

## Installation

PortBoard is not published yet. The intended zero-install command is:

```bash
uvx portboard
```

## Development

The initial implementation will target Python 3.11+ and use:

- [Textual](https://textual.textualize.io/) for the terminal UI
- [psutil](https://psutil.readthedocs.io/) for process and socket discovery
- [HTTPX](https://www.python-httpx.org/) for health checks
- `pytest` for tests

Once the first implementation lands, local development will use:

```bash
uv sync
uv run portboard --json
uv run pytest
```

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for the proposed milestones. The product brief is
also available in [Chinese](./docs/idea.zh-CN.md).

The target module boundaries, dependency rules, and implementation order are
defined in the [architecture document](./docs/architecture.md).

## Contributing

Ideas and early feedback are welcome through GitHub Issues. Contribution
guidelines will be added with the first working prototype.

## License

[MIT](./LICENSE)
