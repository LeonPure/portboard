"""Use case for assembling a resilient local-service snapshot."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from portboard.application.contracts import ListenerScanner, ProjectResolver, ServiceProbe
from portboard.domain.models import (
    HealthInfo,
    Listener,
    ProcessInfo,
    ProjectInfo,
    ScanWarning,
    Service,
    ServiceSnapshot,
)


class DiscoverServices:
    """Combine system listeners with process and Git project information."""

    def __init__(
        self,
        scanner: ListenerScanner,
        project_resolver: ProjectResolver,
        service_probe: ServiceProbe | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._scanner = scanner
        self._project_resolver = project_resolver
        self._service_probe = service_probe
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(self) -> ServiceSnapshot:
        """Return a snapshot without losing services to per-item failures."""
        scan = self._scanner.scan()
        listeners = scan.listeners
        services: list[Service] = []
        warnings: list[ScanWarning] = list(scan.warnings)

        for listener in sorted(listeners, key=_listener_sort_key):
            process = self._find_process(listener, warnings)
            project = self._find_project(listener, process, warnings)
            health = self._find_health(listener, warnings)
            services.append(
                Service(
                    listener=listener,
                    process=process,
                    project=project,
                    health=health,
                )
            )

        return ServiceSnapshot(
            observed_at=self._clock(),
            services=tuple(services),
            warnings=tuple(warnings),
        )

    def _find_process(
        self, listener: Listener, warnings: list[ScanWarning]
    ) -> ProcessInfo | None:
        if listener.pid is None:
            warnings.append(
                ScanWarning(
                    code="process-unavailable",
                    message=f"No process is available for {listener.host}:{listener.port}.",
                )
            )
            return None

        try:
            process = self._scanner.get_process(listener.pid)
        except Exception as error:
            warnings.append(
                ScanWarning(
                    code="process-lookup-failed",
                    message=(
                        f"Could not inspect PID {listener.pid} for "
                        f"{listener.host}:{listener.port}: {error}"
                    ),
                )
            )
            return None

        if process is None:
            warnings.append(
                ScanWarning(
                    code="process-unavailable",
                    message=(
                        f"PID {listener.pid} for {listener.host}:{listener.port} "
                        "is no longer available or cannot be inspected."
                    ),
                )
            )
        return process

    def _find_project(
        self,
        listener: Listener,
        process: ProcessInfo | None,
        warnings: list[ScanWarning],
    ) -> ProjectInfo | None:
        if process is None or process.cwd is None:
            return None

        try:
            return self._project_resolver.resolve(process.cwd)
        except Exception as error:
            warnings.append(
                ScanWarning(
                    code="project-lookup-failed",
                    message=(
                        f"Could not resolve the project for {listener.host}:{listener.port}: "
                        f"{error}"
                    ),
                )
            )
            return None

    def _find_health(
        self, listener: Listener, warnings: list[ScanWarning]
    ) -> HealthInfo | None:
        if self._service_probe is None:
            return None

        try:
            return self._service_probe.probe(listener)
        except Exception as error:
            warnings.append(
                ScanWarning(
                    code="health-probe-failed",
                    message=(
                        f"Could not check {listener.host}:{listener.port}: {error}"
                    ),
                )
            )
            return None


def _listener_sort_key(listener: Listener) -> tuple[int, str, int, str]:
    """Keep output deterministic across operating-system scan ordering."""
    return (listener.port, listener.host, listener.pid or -1, listener.transport.value)
