# PortBoard

> A terminal dashboard for discovering and managing local development services.

PortBoard aims to answer a deceptively simple question:

**What is running on my machine, and where can I access it?**

Modern development often means running a frontend, API, database, containers,
and several forgotten dev servers at the same time. PortBoard brings them into
one fast, readable terminal interface.

> [!NOTE]
> PortBoard is currently an early alpha. The core discovery and terminal
> workflows are implemented, but the public interfaces may still evolve.

## Current prototype

PortBoard has a live terminal dashboard with manual refresh, filtering, and sorting:

```bash
uv run portboard
```

Keyboard shortcuts in the dashboard:

- `r`: refresh now; `f` / `Esc`: focus or clear the filter.
- `p`, `o`, `n`: sort by project, port, or process; press again to reverse.
- `Enter` or `d`: show complete details for the selected service.
- `w`: show scan warnings and their full diagnostic messages.
- `c`: copy the selected HTTP service URL; `b`: open it in the default browser.
- `x`: request to stop the selected process. PortBoard shows the PID, command,
  and port, requires confirmation, then revalidates the process before sending
  the termination request.
- `q`: quit.

The dashboard scans once on startup, then refreshes only when you press `r`.
To retain periodic refresh for a long-running view, opt in with an interval:

```bash
uv run portboard --refresh-seconds 3
```

HTTP listeners display their response status and probe latency; a 4xx or 5xx
response is unhealthy but is still an identified HTTP endpoint that can be
copied or opened. Other TCP listeners remain visible with a `listening` status
and no latency value.

When Docker is available, PortBoard also labels a host listener with the
matching running container and its internal port. Missing Docker installations
or inaccessible Docker daemons only add a warning; they do not stop discovery.

For HTTP services bound to a LAN-reachable interface, press `l` to show a QR
code for the selected LAN URL. Scan it from a phone or tablet on the same
network.

The same discovery snapshot is also available as versioned JSON output for
scripts and bug reports:

```bash
uv run portboard --json
```

It reports visible TCP listeners together with best-effort process metadata,
their nearest Git project, and HTTP response status when a service responds to
a short local probe. When the operating system restricts access to an
individual process, the command preserves the remaining results and reports a
warning. If both system listener discovery paths are unavailable, JSON mode
exits non-zero instead of returning a misleading empty snapshot.

## Current experience

```text
┌ Project       Port    Status    Process       URL
│ my-blog       3000    healthy   node          http://localhost:3000
│ shop-api      8000    healthy   uvicorn       http://localhost:8000
│ postgres      5432    running   docker        localhost:5432
│ old-project   5173    unhealthy vite          http://localhost:5173
└
```

The current alpha can:

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

The implementation targets Python 3.11+ and uses:

- [Textual](https://textual.textualize.io/) for the terminal UI
- [psutil](https://psutil.readthedocs.io/) for process and socket discovery
- [HTTPX](https://www.python-httpx.org/) for health checks
- `pytest` for tests

Local development uses:

```bash
uv sync
uv run portboard --json
uv run ruff check .
uv run mypy
uv run pytest
uv build
```

CI runs the same checks on macOS and Linux with Python 3.11 and 3.13.

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for the proposed milestones. The product brief is
also available in [Chinese](./docs/idea.zh-CN.md).

The target module boundaries, dependency rules, and implementation order are
defined in the [architecture document](./docs/architecture.md).

## Contributing

Ideas, bug reports, and contributions are welcome through GitHub Issues and
pull requests.

## License

[MIT](./LICENSE)
