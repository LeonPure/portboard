"""User-initiated local-service actions with explicit safety boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from portboard.application.contracts import DesktopController, ProcessController
from portboard.domain.models import Service


@dataclass(frozen=True, slots=True)
class ActionResult:
    """A displayable result from a requested service action."""

    succeeded: bool
    message: str


class ServiceActions:
    """Open, copy, and safely stop services selected by a presentation layer."""

    def __init__(
        self,
        desktop: DesktopController,
        process_controller: ProcessController,
    ) -> None:
        self._desktop = desktop
        self._process_controller = process_controller

    def copy_url(self, service: Service) -> ActionResult:
        """Copy an identified HTTP URL to the system clipboard."""
        url = service_url(service)
        if url is None:
            return ActionResult(False, "The selected service has no HTTP URL.")
        try:
            self._desktop.copy_text(url)
        except Exception as error:
            return ActionResult(False, f"Could not copy URL: {error}")
        return ActionResult(True, f"Copied {url}")

    def open_url(self, service: Service) -> ActionResult:
        """Open an identified HTTP URL in the user's default browser."""
        url = service_url(service)
        if url is None:
            return ActionResult(False, "The selected service has no HTTP URL.")
        try:
            self._desktop.open_url(url)
        except Exception as error:
            return ActionResult(False, f"Could not open URL: {error}")
        return ActionResult(True, f"Opened {url}")

    def stop(self, service: Service) -> ActionResult:
        """Terminate a process only after the caller obtains user confirmation."""
        if service.process is None:
            return ActionResult(False, "The selected service has no inspectable process.")
        try:
            terminated = self._process_controller.terminate_if_matches(service.process)
        except Exception as error:
            return ActionResult(False, f"Could not stop PID {service.process.pid}: {error}")
        if not terminated:
            return ActionResult(
                False,
                f"PID {service.process.pid} changed, exited, or could not be revalidated.",
            )
        return ActionResult(True, f"Requested termination of PID {service.process.pid}.")


def service_url(service: Service) -> str | None:
    """Return a browser-safe URL only for listeners identified as HTTP."""
    if service.health is None or service.health.protocol != "http":
        return None

    host = service.listener.host
    if host == "0.0.0.0":
        host = "127.0.0.1"
    elif host == "::":
        host = "::1"
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"http://{host}:{service.listener.port}"
