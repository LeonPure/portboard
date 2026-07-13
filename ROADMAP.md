# Roadmap

This roadmap describes the current direction, not a promise of release dates.

## 0.1 — Discover

Status: implemented in the current alpha.

- Discover TCP listeners on macOS and Linux.
- Associate ports with processes, commands, and working directories.
- Detect the nearest Git repository.
- Render a live, keyboard-driven terminal table.
- Add JSON output for scripts and bug reports.

## 0.2 — Inspect and act

Status: implemented in the current alpha.

- Probe HTTP services and show response status and latency.
- Copy URLs and open them in the default browser.
- Stop a process after explicit confirmation.
- Filter and sort by project, port, process, and health.

## 0.3 — Containers and devices

Status: implemented in the current alpha.

- Show Docker container and port mapping information.
- Display LAN URLs for services bound to accessible interfaces.
- Render QR codes for testing from phones and tablets.

## 0.4 — Reliability and maintainability

Status: implemented in the current alpha.

- Keep discovery off the TUI event loop and coalesce repeated refresh requests.
- Bound concurrent HTTP probes and preserve deterministic output ordering.
- Revalidate process identity using its creation time before termination.
- Separate fatal discovery failures from degradable enrichment warnings.
- Add warning details, architecture checks, cross-platform CI, Ruff, and mypy.

## Later explorations

- Stable `project.localhost` aliases.
- Saved project groups and favorites.
- Port conflict notifications.
- Optional web and system tray interfaces.

## Non-goals for the first releases

- Replacing a full process supervisor.
- Managing production services.
- Automatically terminating processes without confirmation.
- Requiring projects to adopt a PortBoard-specific configuration format.
