"""Interfaces the application layer needs from the outside world."""

from __future__ import annotations

from typing import Protocol

from portboard.domain.models import HealthInfo, Listener, ListenerScan, ProcessInfo, ProjectInfo


class ListenerScanner(Protocol):
    """Reads listeners and process metadata from the local operating system."""

    def scan(self) -> ListenerScan:
        """Return the TCP listeners visible to the current user."""

    def get_process(self, pid: int) -> ProcessInfo | None:
        """Return best-effort metadata for a process, if it is still available."""


class ProjectResolver(Protocol):
    """Resolves a process working directory to its nearest Git project."""

    def resolve(self, cwd: str) -> ProjectInfo | None:
        """Return the Git project containing *cwd*, if there is one."""


class ServiceProbe(Protocol):
    """Identifies and checks optional protocols exposed by a listener."""

    def probe(self, listener: Listener) -> HealthInfo | None:
        """Return HTTP health information when the listener responds to HTTP."""


class DesktopController(Protocol):
    """Performs user-requested browser and clipboard operations."""

    def open_url(self, url: str) -> None:
        """Open *url* in the user's default browser."""

    def copy_text(self, text: str) -> None:
        """Copy *text* to the system clipboard."""


class ProcessController(Protocol):
    """Performs guarded process actions on the local operating system."""

    def terminate_if_matches(self, expected: ProcessInfo) -> bool:
        """Revalidate *expected* immediately before requesting termination."""
