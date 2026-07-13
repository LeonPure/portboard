# Changelog

All notable changes to PortBoard are documented here. The project follows
[Semantic Versioning](https://semver.org/) and uses Python-compatible pre-release
versions.

## [Unreleased]

## [0.1.0a1] - 2026-07-13

### Added

- Discover TCP listeners with process, command, working-directory, and Git metadata.
- Identify HTTP services and report response status and latency.
- Display Docker port mappings, LAN URLs, and terminal QR codes.
- Provide a keyboard-driven Textual dashboard with filtering, sorting, details,
  warnings, manual refresh, and optional periodic refresh.
- Copy and open HTTP URLs and safely stop revalidated local processes.
- Export versioned JSON for scripts and diagnostics.
- Test macOS and Linux with Python 3.11 and 3.13 in CI.

### Security

- Require explicit confirmation and process creation-time validation before
  terminating a process.

[Unreleased]: https://github.com/LeonPure/portboard/compare/v0.1.0a1...HEAD
[0.1.0a1]: https://github.com/LeonPure/portboard/releases/tag/v0.1.0a1
