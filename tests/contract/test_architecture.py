"""Executable dependency rules for PortBoard's inward-facing architecture."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).parents[2] / "src" / "portboard"
ALLOWED_DEPENDENCIES = {
    "domain": set(),
    "application": {"application", "domain"},
    "adapters": {"adapters", "application", "domain"},
    "presentation": {"presentation", "application", "domain"},
}


def test_layer_dependencies_only_point_inward() -> None:
    violations: list[str] = []
    for layer, allowed_layers in ALLOWED_DEPENDENCIES.items():
        for path in (SOURCE_ROOT / layer).rglob("*.py"):
            for imported_layer in _portboard_layers_imported_by(path):
                if imported_layer not in allowed_layers:
                    violations.append(
                        f"{path.relative_to(SOURCE_ROOT)} imports {imported_layer}"
                    )

    assert violations == []


def _portboard_layers_imported_by(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    layers: set[str] = set()
    for node in ast.walk(tree):
        module: str | None = None
        if isinstance(node, ast.ImportFrom):
            module = node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                _add_layer(alias.name, layers)
        if module is not None:
            _add_layer(module, layers)
    return layers


def _add_layer(module: str, layers: set[str]) -> None:
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "portboard":
        layers.add(parts[1])
