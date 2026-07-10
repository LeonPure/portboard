"""Interfaces the application layer needs from the outside world."""

from __future__ import annotations

from typing import Protocol

from portboard.domain.models import ListenerScan, ProcessInfo, ProjectInfo


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
