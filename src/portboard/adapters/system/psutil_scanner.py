"""psutil-backed TCP listener and process discovery."""

from __future__ import annotations

import shlex
from collections.abc import Callable, Iterable
from typing import Any, TypeVar, cast

import psutil

from portboard.domain.models import Listener, ListenerScan, ProcessInfo, ScanWarning

T = TypeVar("T")


class PsutilListenerScanner:
    """Discover the listeners visible to the process running PortBoard."""

    def scan(self) -> ListenerScan:
        try:
            connections = psutil.net_connections(kind="tcp")
        except (psutil.Error, OSError) as error:
            return self._scan_processes_after_global_failure(error)

        listeners = _listeners_from_connections(connections)
        return ListenerScan(listeners=_sort_listeners(listeners))

    def _scan_processes_after_global_failure(self, error: Exception) -> ListenerScan:
        """Recover when a protected process aborts a global socket scan."""
        listeners: set[Listener] = set()
        try:
            for process in psutil.process_iter():
                try:
                    connections = process.net_connections(kind="tcp")
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue
                listeners.update(_listeners_from_connections(connections, pid=process.pid))
        except (psutil.Error, OSError) as fallback_error:
            raise OSError(
                "TCP listener discovery was unavailable "
                f"({error}); fallback scanning also failed ({fallback_error})."
            ) from fallback_error

        return ListenerScan(
            listeners=_sort_listeners(listeners),
            warnings=(
                ScanWarning(
                    code="system-scan-partial",
                    message=(
                        "Global socket discovery was unavailable "
                        f"({error}); showing listeners visible process by process."
                    ),
                ),
            ),
        )

    def get_process(self, pid: int) -> ProcessInfo | None:
        try:
            process = psutil.Process(pid)
            name = _read_process_field(process.name)
            command_parts = _read_process_field(process.cmdline)
            cwd = _read_process_field(process.cwd)
            create_time = _read_process_field(process.create_time)
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            return None

        command = shlex.join(command_parts) if command_parts else None
        return ProcessInfo(
            pid=pid,
            name=name,
            command=command,
            cwd=cwd,
            create_time=create_time,
        )


def _listeners_from_connections(
    connections: Iterable[Any], *, pid: int | None = None
) -> set[Listener]:
    listeners: set[Listener] = set()
    for connection in connections:
        if connection.status != psutil.CONN_LISTEN or not connection.laddr:
            continue

        host, port = _address_parts(connection.laddr)
        listeners.add(Listener(host=host, port=port, pid=pid or connection.pid))
    return listeners


def _sort_listeners(listeners: set[Listener]) -> tuple[Listener, ...]:
    return tuple(sorted(listeners, key=lambda item: (item.port, item.host, item.pid or -1)))


def _address_parts(address: object) -> tuple[str, int]:
    """Handle psutil's platform-specific address tuple variants."""
    host = getattr(address, "ip", None)
    port = getattr(address, "port", None)
    if host is not None and port is not None:
        return str(host), int(port)

    host, port = cast(tuple[Any, Any], address)
    return str(host), int(port)


def _read_process_field(reader: Callable[[], T]) -> T | None:
    """Return ``None`` for an inaccessible optional process field."""
    try:
        return reader()
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
        return None
