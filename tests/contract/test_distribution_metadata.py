"""Keep the Python and npm distribution metadata on one logical version."""

from __future__ import annotations

import json
import re
from pathlib import Path

from portboard import __version__

PROJECT_ROOT = Path(__file__).parents[2]
NPM_ROOT = PROJECT_ROOT / "packaging" / "npm"
TARGETS = ("darwin-arm64", "darwin-x64", "linux-arm64", "linux-x64")


def test_npm_packages_match_the_python_release_version() -> None:
    npm_version = _npm_version(__version__)
    launcher = _package_json(NPM_ROOT / "portboard" / "package.json")

    assert launcher["version"] == npm_version
    assert launcher["optionalDependencies"] == {
        f"@leonpure/portboard-{target}": npm_version for target in TARGETS
    }

    for target in TARGETS:
        package = _package_json(NPM_ROOT / "platforms" / target / "package.json")
        assert package["name"] == f"@leonpure/portboard-{target}"
        assert package["version"] == npm_version


def test_npm_platform_constraints_match_the_package_names() -> None:
    for target in TARGETS:
        operating_system, architecture = target.split("-", maxsplit=1)
        package = _package_json(NPM_ROOT / "platforms" / target / "package.json")

        assert package["os"] == [operating_system]
        assert package["cpu"] == [architecture]


def _package_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _npm_version(python_version: str) -> str:
    match = re.fullmatch(r"(\d+\.\d+\.\d+)(?:(a|b|rc)(\d+))?", python_version)
    if match is None:
        raise AssertionError(f"Unsupported release version: {python_version}")

    release, phase, number = match.groups()
    if phase is None:
        return release
    npm_phase = {"a": "alpha", "b": "beta", "rc": "rc"}[phase]
    return f"{release}-{npm_phase}.{number}"
