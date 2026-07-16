"""Textual dashboard orchestration for PortBoard service discovery."""

from __future__ import annotations

from datetime import UTC
from typing import Literal, Protocol

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Header, Input, LoadingIndicator, Static
from textual.worker import Worker, WorkerState

from portboard.application.actions import ActionResult, ServiceActions
from portboard.domain.models import Service, ServiceSnapshot
from portboard.presentation.tui.formatters import (
    container_label as _container,
    endpoint as _endpoint,
    latency as _latency,
    qr_text as _qr_text,
    refresh_status as _refresh_status,
    service_key as _service_key,
    status as _status,
    truncate as _truncate,
)
from portboard.presentation.tui.screens import (
    LanQrScreen,
    ServiceDetailScreen,
    StopConfirmationScreen,
    WarningsScreen,
)
from portboard.presentation.tui.state import DashboardState
from portboard.presentation.tui.widgets import (
    KeyboardServiceTable,
    ShortcutFooter,
    shortcut_footer_text as _shortcut_footer_text,
)

__all__ = [
    "PortBoardApp",
    "_qr_text",
    "_refresh_status",
    "_shortcut_footer_text",
    "_truncate",
]


class ServiceDiscoverer(Protocol):
    """The discovery use case consumed by the terminal dashboard."""

    def execute(self) -> ServiceSnapshot:
        """Return the most recent local-service snapshot."""


class PortBoardApp(App[None]):
    """Display, filter, sort, and optionally refresh local services."""

    TITLE = "PortBoard"
    CSS_PATH = "portboard.tcss"
    BINDINGS = [
        Binding("r", "refresh", "View: Refresh"),
        Binding("f", "focus_filter", "View: Filter"),
        Binding("escape", "clear_filter", "View: Clear"),
        Binding("d", "show_details", "View: Details"),
        Binding("w", "show_warnings", "View: Warnings"),
        Binding("q", "quit", "View: Quit"),
        Binding("p", "sort_by_project", "Sort: Project"),
        Binding("o", "sort_by_port", "Sort: Port"),
        Binding("n", "sort_by_process", "Sort: Process"),
        Binding("c", "copy_url", "Service: Copy"),
        Binding("b", "open_url", "Service: Open"),
        Binding("x", "request_stop", "Service: Stop"),
        Binding("l", "show_lan_qr", "Service: LAN QR"),
    ]

    def __init__(
        self,
        discover: ServiceDiscoverer,
        actions: ServiceActions,
        *,
        refresh_interval: float | None = None,
    ) -> None:
        super().__init__()
        self._discover = discover
        self._actions = actions
        self._refresh_interval = refresh_interval
        self._state = DashboardState()
        self._visible_services: dict[str, Service] = {}
        self._refresh_worker: Worker[ServiceSnapshot] | None = None
        self._refresh_pending = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Input(
            placeholder="Filter by project, port, process, command, or address",
            id="filter",
        )
        yield Horizontal(
            LoadingIndicator(),
            Static("Scanning local ports and checking services…", id="loading-message"),
            id="loading",
        )
        yield KeyboardServiceTable(id="services", cell_padding=0)
        yield Static(id="status")
        yield ShortcutFooter(id="shortcuts")

    def on_mount(self) -> None:
        table = self.query_one("#services", DataTable)
        table.add_column("Project", key="project", width=15)
        table.add_column("Port", key="port", width=6)
        table.add_column("Status", key="status", width=15)
        table.add_column("Latency", key="latency", width=9)
        table.add_column("Process", key="process", width=16)
        table.add_column("Command", key="command", width=32)
        table.add_column("Endpoint", key="endpoint", width=24)
        table.add_column("Container", key="container", width=16)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.focus()
        self._request_refresh()
        if self._refresh_interval is not None:
            self.set_interval(self._refresh_interval, self._request_refresh)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._state.set_filter(event.value)
        self._render_services()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker is not self._refresh_worker:
            return
        if event.state not in {WorkerState.ERROR, WorkerState.SUCCESS}:
            return

        worker = self._refresh_worker
        self._refresh_worker = None
        self._set_initial_loading(False)
        dashboard_mounted = self._dashboard_is_mounted()
        if event.state is WorkerState.SUCCESS and worker.result is not None:
            self._state.snapshot = worker.result
            if dashboard_mounted:
                self._render_services()
        elif dashboard_mounted:
            self.query_one("#status", Static).update(
                f"Refresh failed: {worker.error or 'unknown error'}"
            )

        if self._refresh_pending:
            self._refresh_pending = False
            if dashboard_mounted:
                self._request_refresh()

    def action_refresh(self) -> None:
        self._request_refresh()

    def action_focus_filter(self) -> None:
        self.query_one("#filter", Input).focus()

    def action_clear_filter(self) -> None:
        self.query_one("#filter", Input).value = ""
        self.query_one("#services", DataTable).focus()

    def action_sort_by_project(self) -> None:
        self._set_sort("project")

    def action_sort_by_port(self) -> None:
        self._set_sort("port")

    def action_sort_by_process(self) -> None:
        self._set_sort("process")

    def action_copy_url(self) -> None:
        service = self._selected_service()
        if service is not None:
            self._report_action(self._actions.copy_url(service))

    def action_open_url(self) -> None:
        service = self._selected_service()
        if service is not None:
            self._report_action(self._actions.open_url(service))

    def action_request_stop(self) -> None:
        service = self._selected_service()
        if service is None:
            return
        if service.process is None:
            self.notify(
                "The selected service has no inspectable process.",
                severity="warning",
            )
            return
        if service.process.create_time is None:
            self.notify(
                "The selected process has no stable start time and cannot be stopped safely.",
                severity="warning",
            )
            return
        self.push_screen(
            StopConfirmationScreen(service),
            lambda confirmed: self._stop_after_confirmation(service, confirmed),
        )

    def action_show_lan_qr(self) -> None:
        service = self._selected_service()
        if service is None:
            return
        if not service.lan_urls:
            self.notify(
                "The selected service has no LAN-accessible HTTP URL.",
                severity="warning",
            )
            return
        self.push_screen(LanQrScreen(service.lan_urls[0]))

    def action_show_details(self) -> None:
        service = self._selected_service()
        if service is not None:
            self.push_screen(ServiceDetailScreen(service))

    def action_show_warnings(self) -> None:
        snapshot = self._state.snapshot
        if snapshot is None or not snapshot.warnings:
            self.notify("The latest scan has no warnings.", severity="information")
            return
        self.push_screen(WarningsScreen(snapshot.warnings))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "services":
            self.action_show_details()

    def _set_sort(self, field: str) -> None:
        self._state.toggle_sort(field)
        self._render_services()

    def _request_refresh(self) -> None:
        if self._refresh_worker is not None and not self._refresh_worker.is_finished:
            self._refresh_pending = True
            return
        if self._state.snapshot is None:
            self._set_initial_loading(True)
            refresh_message = "Scanning local ports and checking services…"
        else:
            refresh_message = "Refreshing local services…"
        self.query_one("#status", Static).update(refresh_message)
        self._refresh_worker = self.run_worker(
            self._discover.execute,
            name="service-discovery",
            group="service-discovery",
            exit_on_error=False,
            thread=True,
        )

    def _set_initial_loading(self, visible: bool) -> None:
        """Update the loading banner if the dashboard is still mounted."""
        for loading in self.query("#loading"):
            loading.display = visible

    def _dashboard_is_mounted(self) -> bool:
        """Return whether refresh results can still be rendered safely."""
        return any(True for _ in self.query("#services"))

    def _render_services(self) -> None:
        snapshot = self._state.snapshot
        if snapshot is None:
            return

        services = self._state.visible_services()
        self._visible_services = {
            _service_key(service): service for service in services
        }
        table = self.query_one("#services", DataTable)
        table.clear()
        for service in services:
            table.add_row(
                _truncate(service.project.name, 15)
                if service.project is not None
                else "—",
                str(service.listener.port),
                _status(service),
                _latency(service),
                _truncate(service.process.name, 16)
                if service.process and service.process.name
                else "—",
                _truncate(service.process.command, 32)
                if service.process and service.process.command
                else "—",
                _truncate(_endpoint(service), 24),
                _truncate(_container(service), 16),
                key=_service_key(service),
            )

        observed_at = snapshot.observed_at.astimezone(UTC).strftime("%H:%M:%SZ")
        warning_count = len(snapshot.warnings)
        warning_text = (
            "no warnings" if warning_count == 0 else f"{warning_count} warning(s)"
        )
        sort_direction = " (descending)" if self._state.sort_reverse else ""
        self.query_one("#status", Static).update(
            f"{len(services)} of {len(snapshot.services)} services · "
            f"updated {observed_at} · {warning_text} · "
            f"{_refresh_status(self._refresh_interval)} · "
            f"sorted by {self._state.sort_field}{sort_direction}"
        )

    def _selected_service(self) -> Service | None:
        table = self.query_one("#services", DataTable)
        if table.row_count == 0:
            self.notify("No service is selected.", severity="warning")
            return None
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        row_key = cell_key.row_key.value
        return self._visible_services.get(row_key) if row_key is not None else None

    def _stop_after_confirmation(
        self, service: Service, confirmed: bool | None
    ) -> None:
        if not confirmed:
            return
        self._report_action(self._actions.stop(service))
        self._request_refresh()

    def _report_action(self, result: ActionResult) -> None:
        severity: Literal["information", "error"] = (
            "information" if result.succeeded else "error"
        )
        self.notify(result.message, severity=severity)
