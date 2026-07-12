"""Live Textual dashboard backed by the service-discovery use case."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC
from typing import Protocol

from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static

from portboard.application.actions import ActionResult, ServiceActions
from portboard.domain.models import HealthStatus, Service, ServiceSnapshot


class ServiceDiscoverer(Protocol):
    """The discovery use case consumed by the terminal dashboard."""

    def execute(self) -> ServiceSnapshot:
        """Return the most recent local-service snapshot."""


class StopConfirmationScreen(ModalScreen[bool]):
    """Require an explicit acknowledgement before terminating a process."""

    CSS = """
    StopConfirmationScreen {
        align: center middle;
    }

    #stop-dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 1 2;
        width: 72;
        height: 13;
        border: thick $error;
        background: $surface;
    }

    #stop-question {
        column-span: 2;
        content-align: center middle;
    }

    StopConfirmationScreen Button {
        width: 100%;
    }
    """

    def __init__(self, service: Service) -> None:
        super().__init__()
        self._service = service

    def compose(self) -> ComposeResult:
        """Show exactly which process and service the user is about to stop."""
        process = self._service.process
        assert process is not None
        command = process.command or process.name or "unknown command"
        question = (
            f"Stop PID {process.pid} ({command}) listening on "
            f"{self._service.listener.host}:{self._service.listener.port}?\n"
            "PortBoard will revalidate the process immediately before stopping it."
        )
        yield Grid(
            Label(question, id="stop-question"),
            Button("Stop process", variant="error", id="confirm-stop"),
            Button("Cancel", variant="primary", id="cancel-stop"),
            id="stop-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Return an explicit decision to the dashboard callback."""
        self.dismiss(event.button.id == "confirm-stop")


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
        ("c", "copy_url", "Copy URL"),
        ("b", "open_url", "Open URL"),
        ("x", "request_stop", "Stop process"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        discover: ServiceDiscoverer,
        actions: ServiceActions,
        *,
        refresh_interval: float = 3.0,
    ) -> None:
        super().__init__()
        self._discover = discover
        self._actions = actions
        self._refresh_interval = refresh_interval
        self._snapshot: ServiceSnapshot | None = None
        self._filter_text = ""
        self._sort_field = "port"
        self._sort_reverse = False
        self._visible_services: dict[str, Service] = {}

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
        table.add_columns(
            "Project",
            "Port",
            "Status",
            "Latency",
            "Process",
            "Command",
            "Endpoint",
        )
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

    def action_copy_url(self) -> None:
        """Copy the selected service's HTTP URL when one is available."""
        service = self._selected_service()
        if service is not None:
            self._report_action(self._actions.copy_url(service))

    def action_open_url(self) -> None:
        """Open the selected service's HTTP URL when one is available."""
        service = self._selected_service()
        if service is not None:
            self._report_action(self._actions.open_url(service))

    def action_request_stop(self) -> None:
        """Ask for confirmation before attempting to stop the selected process."""
        service = self._selected_service()
        if service is None:
            return
        if service.process is None:
            self.notify("The selected service has no inspectable process.", severity="warning")
            return
        self.push_screen(
            StopConfirmationScreen(service),
            lambda confirmed: self._stop_after_confirmation(service, confirmed),
        )

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
        self._visible_services = {_service_key(service): service for service in services}
        table = self.query_one("#services", DataTable)
        table.clear()
        for service in services:
            table.add_row(
                service.project.name if service.project is not None else "—",
                str(service.listener.port),
                _status(service),
                _latency(service),
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

    def _selected_service(self) -> Service | None:
        table = self.query_one("#services", DataTable)
        if table.row_count == 0:
            self.notify("No service is selected.", severity="warning")
            return None
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        return self._visible_services.get(cell_key.row_key.value)

    def _stop_after_confirmation(
        self, service: Service, confirmed: bool | None
    ) -> None:
        if not confirmed:
            return
        self._report_action(self._actions.stop(service))
        self._refresh_services()

    def _report_action(self, result: ActionResult) -> None:
        severity = "information" if result.succeeded else "error"
        self.notify(result.message, severity=severity)


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
    """Format a TCP endpoint, including a URL when HTTP was identified."""
    host = service.listener.host
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    endpoint = f"{host}:{service.listener.port}"
    return f"http://{endpoint}" if service.health and service.health.protocol == "http" else endpoint


def _status(service: Service) -> str:
    """Render the best available service status without inventing HTTP health."""
    if service.health is None:
        return "listening"
    label = "healthy" if service.health.status is HealthStatus.HEALTHY else "unhealthy"
    return f"{label} ({service.health.status_code})"


def _latency(service: Service) -> str:
    """Render HTTP probe latency only when a service responded to the probe."""
    if service.health is None:
        return "—"
    return f"{service.health.latency_ms:.1f} ms"


def _service_key(service: Service) -> str:
    """Create a stable table key for the lifetime of one snapshot."""
    return f"{service.listener.host}:{service.listener.port}:{service.listener.pid}"
