# Changelog

All notable changes to PortBoard are documented here. The project follows
[Semantic Versioning](https://semver.org/) and uses Python-compatible pre-release
versions.

## [Unreleased]

## [0.1.0a3] - 2026-07-16

### Added

- Support Windows in the Python distribution and provide standalone x64 and
  ARM64 executables through GitHub Releases and npm.
- Show an explicit loading indicator while the dashboard performs its initial scan.
- Package standalone executables for distribution through the official
  `LeonPure/tap` Homebrew tap.
- Provide a checksum-verifying shell installer for direct GitHub Release
  installations.

## [0.1.0a2] - 2026-07-14

### Added

- Build standalone macOS and Linux executables for arm64 and x64 releases.
- Provide an npm launcher that installs only the native executable for the
  current platform without modifying Python environments.
- Attach release binaries and SHA-256 checksums to GitHub Releases.

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

[Unreleased]: https://github.com/LeonPure/portboard/compare/v0.1.0a3...HEAD
[0.1.0a3]: https://github.com/LeonPure/portboard/compare/v0.1.0a2...v0.1.0a3
[0.1.0a2]: https://github.com/LeonPure/portboard/compare/v0.1.0a1...v0.1.0a2
[0.1.0a1]: https://github.com/LeonPure/portboard/releases/tag/v0.1.0a1
