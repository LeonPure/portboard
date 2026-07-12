"""Composition root for the currently available PortBoard use cases."""

from __future__ import annotations

from portboard.adapters.desktop import SystemDesktopController
from portboard.adapters.http.httpx_probe import HttpxServiceProbe
from portboard.adapters.project.git_resolver import GitProjectResolver
from portboard.adapters.system.psutil_scanner import PsutilListenerScanner
from portboard.adapters.system.process_controller import PsutilProcessController
from portboard.application.actions import ServiceActions
from portboard.application.discover import DiscoverServices


def build_discover_services() -> DiscoverServices:
    """Create the real local-service discovery use case."""
    return DiscoverServices(
        scanner=PsutilListenerScanner(),
        project_resolver=GitProjectResolver(),
        service_probe=HttpxServiceProbe(),
    )


def build_service_actions() -> ServiceActions:
    """Create the real user-requested service actions."""
    return ServiceActions(
        desktop=SystemDesktopController(),
        process_controller=PsutilProcessController(),
    )
