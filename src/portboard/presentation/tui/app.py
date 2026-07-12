"""Live Textual dashboard backed by the service-discovery use case."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC
from typing import Protocol

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Input, Static

from portboard.domain.models import Service, ServiceSnapshot


class ServiceDiscoverer(Protocol):
    """The discovery use case consumed by the terminal dashboard."""

    def execute(self) -> ServiceSnapshot:
        """Return the most recent local-service snapshot."""


class PortBoardApp(App[None]):
    """Display, filter, sort, and periodically refresh local services."""

    TITLE = "PortBoard"
    CSS = """
    #filter {
        margin: 1 2 0 2;
    }

    #services {
        height: 1fr;
        margin: 1 2;
    }

    #status {
        height: auto;
        margin: 0 2 1 2;
        color: $text-muted;
    }
    """
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("f", "focus_filter", "Filter"),
        ("escape", "clear_filter", "Clear filter"),
        ("p", "sort_by_project", "Sort project"),
        ("o", "sort_by_port", "Sort port"),
        ("n", "sort_by_process", "Sort process"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, discover: ServiceDiscoverer, *, refresh_interval: float = 3.0) -> None:
        super().__init__()
        self._discover = discover
        self._refresh_interval = refresh_interval
        self._snapshot: ServiceSnapshot | None = None
        self._filter_text = ""
        self._sort_field = "port"
        self._sort_reverse = False

    def compose(self) -> ComposeResult:
        """Compose the dashboard without performing operating-system access."""
        yield Header(show_clock=False)
        yield Input(placeholder="Filter by project, port, process, command, or address", id="filter")
        yield DataTable(id="services")
        yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Configure the table and start the first scan after mounting."""
        table = self.query_one("#services", DataTable)
        table.add_columns("Project", "Port", "Status", "Process", "Command", "Endpoint")
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.focus()
        self._refresh_services()
        self.set_interval(self._refresh_interval, self._refresh_services)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Apply filtering locally without repeating the system scan."""
        self._filter_text = event.value.casefold().strip()
        self._render_services()

    def action_refresh(self) -> None:
        """Request a fresh snapshot immediately."""
        self._refresh_services()

    def action_focus_filter(self) -> None:
        """Move keyboard input into the filter field."""
        self.query_one("#filter", Input).focus()

    def action_clear_filter(self) -> None:
        """Clear the current filter and return focus to the services table."""
        self.query_one("#filter", Input).value = ""
        self.query_one("#services", DataTable).focus()

    def action_sort_by_project(self) -> None:
        """Sort by project name, reversing on repeated use."""
        self._set_sort("project")

    def action_sort_by_port(self) -> None:
        """Sort by port number, reversing on repeated use."""
        self._set_sort("port")

    def action_sort_by_process(self) -> None:
        """Sort by process name, reversing on repeated use."""
        self._set_sort("process")

    def _set_sort(self, field: str) -> None:
        if self._sort_field == field:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_field = field
            self._sort_reverse = False
        self._render_services()

    def _refresh_services(self) -> None:
        try:
            self._snapshot = self._discover.execute()
        except Exception as error:
            self.query_one("#status", Static).update(f"Refresh failed: {error}")
            return
        self._render_services()

    def _render_services(self) -> None:
        if self._snapshot is None:
            return

        services = tuple(self._sorted_services(self._filtered_services(self._snapshot.services)))
        table = self.query_one("#services", DataTable)
        table.clear()
        for service in services:
            table.add_row(
                service.project.name if service.project is not None else "—",
                str(service.listener.port),
                "listening",
                service.process.name if service.process and service.process.name else "—",
                service.process.command if service.process and service.process.command else "—",
                _endpoint(service),
                key=_service_key(service),
            )

        observed_at = self._snapshot.observed_at.astimezone(UTC).strftime("%H:%M:%SZ")
        warning_count = len(self._snapshot.warnings)
        warning_text = "no warnings" if warning_count == 0 else f"{warning_count} warning(s)"
        self.query_one("#status", Static).update(
            f"{len(services)} of {len(self._snapshot.services)} services · "
            f"updated {observed_at} · {warning_text} · "
            f"sorted by {self._sort_field}{' (descending)' if self._sort_reverse else ''}"
        )

    def _filtered_services(self, services: Iterable[Service]) -> Iterable[Service]:
        if not self._filter_text:
            return services
        return (
            service
            for service in services
            if self._filter_text in _searchable_text(service).casefold()
        )

    def _sorted_services(self, services: Iterable[Service]) -> list[Service]:
        return sorted(services, key=lambda service: _sort_key(service, self._sort_field), reverse=self._sort_reverse)


def _searchable_text(service: Service) -> str:
    """Return user-facing service fields that should match the filter."""
    return " ".join(
        value
        for value in (
            service.listener.host,
            str(service.listener.port),
            service.process.name if service.process else None,
            service.process.command if service.process else None,
            service.process.cwd if service.process else None,
            service.project.name if service.project else None,
            service.project.root if service.project else None,
        )
        if value is not None
    )


def _sort_key(service: Service, field: str) -> tuple[str, int]:
    """Return a deterministic key for each supported user sort."""
    if field == "port":
        return ("", service.listener.port)
    if field == "project":
        return (service.project.name.casefold() if service.project else "", service.listener.port)
    return (
        service.process.name.casefold() if service.process and service.process.name else "",
        service.listener.port,
    )


def _endpoint(service: Service) -> str:
    """Format a TCP endpoint without assuming that every listener is HTTP."""
    host = service.listener.host
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"{host}:{service.listener.port}"


def _service_key(service: Service) -> str:
    """Create a stable table key for the lifetime of one snapshot."""
    return f"{service.listener.host}:{service.listener.port}:{service.listener.pid}"
