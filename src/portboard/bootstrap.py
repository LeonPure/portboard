"""Composition root for the currently available PortBoard use cases."""

from __future__ import annotations

from portboard.adapters.project.git_resolver import GitProjectResolver
from portboard.adapters.system.psutil_scanner import PsutilListenerScanner
from portboard.application.discover import DiscoverServices


def build_discover_services() -> DiscoverServices:
    """Create the real local-service discovery use case."""
    return DiscoverServices(
        scanner=PsutilListenerScanner(),
        project_resolver=GitProjectResolver(),
    )
