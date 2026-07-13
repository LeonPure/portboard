"""Modal screens used by the PortBoard dashboard."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from portboard.domain.models import ScanWarning, Service
from portboard.presentation.tui.formatters import (
    qr_text,
    service_details,
    warnings_details,
)


class StopConfirmationScreen(ModalScreen[bool]):
    """Require an explicit acknowledgement before terminating a process."""

    BINDINGS = [
        ("left", "focus_cancel", "Cancel"),
        ("right", "focus_confirm", "Stop"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, service: Service) -> None:
        super().__init__()
        self._service = service

    def compose(self) -> ComposeResult:
        process = self._service.process
        assert process is not None
        command = process.command or process.name or "unknown command"
        process_details = (
            f"PID       {process.pid}\n"
            f"Command   {command}\n"
            f"Listener  {self._service.listener.host}:{self._service.listener.port}"
        )
        yield Grid(
            Label("Stop process?", id="stop-title"),
            Label("This will stop the selected local service.", id="stop-warning"),
            Static(process_details, id="stop-process"),
            Button("Cancel  [Esc]", id="cancel-stop", flat=True),
            Button(
                "Stop process  [Enter]",
                variant="primary",
                id="confirm-stop",
                flat=True,
            ),
            id="stop-dialog",
        )

    def on_mount(self) -> None:
        self.query_one("#cancel-stop", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-stop")

    def action_focus_cancel(self) -> None:
        self.query_one("#cancel-stop", Button).focus()

    def action_focus_confirm(self) -> None:
        self.query_one("#confirm-stop", Button).focus()

    def action_cancel(self) -> None:
        self.dismiss(False)


class LanQrScreen(ModalScreen[None]):
    """Show a terminal-rendered QR code for a LAN-accessible service URL."""

    def __init__(self, url: str) -> None:
        super().__init__()
        self._url = url

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(self._url, id="lan-qr-url"),
            Static(qr_text(self._url), id="lan-qr-code"),
            Label("Press Esc to close", id="lan-qr-close"),
            id="lan-qr-dialog",
        )

    def key_escape(self) -> None:
        self.dismiss()


class ServiceDetailScreen(ModalScreen[None]):
    """Show every available field for the service selected in the overview."""

    def __init__(self, service: Service) -> None:
        super().__init__()
        self._service = service

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Static(service_details(self._service), id="service-detail-content"),
            Label("Press Esc to close"),
            id="service-details",
        )

    def key_escape(self) -> None:
        self.dismiss()


class WarningsScreen(ModalScreen[None]):
    """Show every non-fatal warning from the latest service snapshot."""

    def __init__(self, warnings: tuple[ScanWarning, ...]) -> None:
        super().__init__()
        self._warnings = warnings

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Label(f"Discovery warnings ({len(self._warnings)})", id="warnings-title"),
            Static(warnings_details(self._warnings), id="warnings-content"),
            Label("Press Esc to close"),
            id="warnings-dialog",
        )

    def key_escape(self) -> None:
        self.dismiss()
