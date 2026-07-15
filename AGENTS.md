# Repository Guidelines

## Project Structure & Module Organization

PortBoard is a Python 3.11+ project using a `src` layout. Production code lives in `src/portboard/`: `domain/` contains dependency-free models, `application/` owns use cases and external contracts, `adapters/` integrates psutil, Git, and other tools, and `presentation/` formats output. `bootstrap.py` wires implementations together; `cli.py` and `__main__.py` are thin entry points.

Tests are organized by purpose: `tests/unit/` for isolated behavior with fakes, `tests/integration/` for operating-system boundaries, and `tests/contract/` for stable JSON/CLI interfaces. Product and architecture decisions belong in `docs/`; consult `docs/architecture.md` before changing module boundaries.

## Build, Test, and Development Commands

- `uv sync`: create the virtual environment and install runtime/dev dependencies.
- `uv run portboard --json`: run the current local-service discovery workflow.
- `uv run ruff check .`: run the configured lint checks.
- `uv run mypy`: run static type checking.
- `uv run pytest`: execute the complete test suite.
- `uv run pytest tests/unit/test_discover.py`: run one focused test module.
- `uv build`: build source and wheel distributions through Hatchling.

## Coding Style & Naming Conventions

Use four-space indentation, type annotations, and modern Python 3.11 syntax. Name modules, functions, and variables with `snake_case`; classes with `PascalCase`; constants with `UPPER_SNAKE_CASE`. Prefer immutable `@dataclass(frozen=True, slots=True)` domain values. Keep domain code free of third-party imports and keep presentation code away from direct OS access. Ruff and mypy are required checks; also follow the existing import grouping and concise docstring patterns.

## Testing Guidelines

Use pytest and name files `test_*.py` and tests `test_<behavior>`. Add deterministic unit tests for application logic, integration tests for adapter behavior, and contract tests for serialized output. There is no numeric coverage threshold, but every behavior change should include regression coverage. Preserve partial results when process or project metadata is inaccessible, and assert the corresponding warning.

## Commit & Pull Request Guidelines

Follow Conventional Commits, as in `feat: add JSON local service discovery`. Use an imperative, focused subject under 72 characters and keep each commit to one logical change. Pull requests should explain intent, architecture impact, and validation commands; link relevant issues. Include representative JSON output for schema changes and screenshots for future TUI changes. Call out macOS/Linux-specific behavior and never commit credentials, virtual environments, caches, or captured process data.

## Branching & Release Workflow

`develop` is the default integration branch. Create focused topic branches and open feature, fix, and documentation pull requests against `develop`; squash-merge each logical change after the required CI checks and owner review pass.

`main` is the release branch. It only accepts owner-approved release pull requests from the repository's `develop` branch, and those pull requests use merge commits. Do not open feature branches directly against `main` or publish from commits that are not already contained in `main`.

Only the repository owner performs releases. Release preparation must follow [`docs/releasing.md`](docs/releasing.md), which is the canonical checklist. Keep the Python version, all npm package versions, and `CHANGELOG.md` in sync. A protected `v*` tag created from the `main` release commit starts the automated GitHub Release, PyPI, and npm workflow; PyPI and npm still require owner approval, and Homebrew is updated through its separate owner-reviewed tap workflow. Never create or push release tags, approve deployment environments, publish packages, or trigger the Homebrew release workflow unless the owner explicitly requests that release action.

## Safety and Compatibility

Treat JSON as a versioned public contract. Destructive process actions must require explicit confirmation and revalidate the PID immediately before execution. Optional integrations should degrade to warnings rather than aborting an otherwise useful scan.
