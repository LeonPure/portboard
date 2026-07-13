"""Use case for assembling a resilient local-service snapshot."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from portboard.application.contracts import (
    ContainerScanner,
    LanAddressResolver,
    ListenerScanner,
    ProjectResolver,
    ServiceProbe,
)
from portboard.application.errors import DiscoveryUnavailable
from portboard.domain.models import (
    ContainerInfo,
    ContainerPortMapping,
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
        container_scanner: ContainerScanner | None = None,
        lan_address_resolver: LanAddressResolver | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
        probe_workers: int = 8,
    ) -> None:
        self._scanner = scanner
        self._project_resolver = project_resolver
        self._service_probe = service_probe
        self._container_scanner = container_scanner
        self._lan_address_resolver = lan_address_resolver
        self._clock = clock or (lambda: datetime.now(UTC))
        self._probe_workers = max(1, probe_workers)

    def execute(self) -> ServiceSnapshot:
        """Return a snapshot without losing services to per-item failures."""
        try:
            scan = self._scanner.scan()
        except Exception as error:
            raise DiscoveryUnavailable(
                f"Could not scan local TCP listeners: {error}"
            ) from error
        listeners = scan.listeners
        services: list[Service] = []
        warnings: list[ScanWarning] = list(scan.warnings)
        container_mappings = self._find_container_mappings(warnings)
        lan_addresses = self._find_lan_addresses(warnings)

        ordered_listeners = tuple(sorted(listeners, key=_listener_sort_key))
        core_services: list[tuple[Listener, ProcessInfo | None, ProjectInfo | None]] = []
        for listener in ordered_listeners:
            process = self._find_process(listener, warnings)
            project = self._find_project(listener, process, warnings)
            core_services.append((listener, process, project))

        health_results = self._find_health_results(ordered_listeners, warnings)

        for (listener, process, project), health in zip(
            core_services, health_results
        ):
            container = _container_for_listener(listener, container_mappings)
            lan_urls = _lan_urls(listener, health, lan_addresses)
            services.append(
                Service(
                    listener=listener,
                    process=process,
                    project=project,
                    health=health,
                    container=container,
                    lan_urls=lan_urls,
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

    def _find_health_results(
        self,
        listeners: tuple[Listener, ...],
        warnings: list[ScanWarning],
    ) -> tuple[HealthInfo | None, ...]:
        if self._service_probe is None:
            return tuple(None for _ in listeners)
        if not listeners:
            return ()

        worker_count = min(self._probe_workers, len(listeners))
        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="portboard-http",
        ) as executor:
            results = tuple(executor.map(self._probe_listener, listeners))

        health_results: list[HealthInfo | None] = []
        for health, warning in results:
            health_results.append(health)
            if warning is not None:
                warnings.append(warning)
        return tuple(health_results)

    def _probe_listener(
        self, listener: Listener
    ) -> tuple[HealthInfo | None, ScanWarning | None]:
        assert self._service_probe is not None
        try:
            return self._service_probe.probe(listener), None
        except Exception as error:
            return None, ScanWarning(
                code="health-probe-failed",
                message=f"Could not check {listener.host}:{listener.port}: {error}",
            )

    def _find_container_mappings(
        self, warnings: list[ScanWarning]
    ) -> tuple[ContainerPortMapping, ...]:
        if self._container_scanner is None:
            return ()
        try:
            scan = self._container_scanner.scan()
        except Exception as error:
            warnings.append(
                ScanWarning(
                    code="container-scan-failed",
                    message=f"Could not inspect Docker containers: {error}",
                )
            )
            return ()
        warnings.extend(scan.warnings)
        return scan.mappings

    def _find_lan_addresses(self, warnings: list[ScanWarning]) -> tuple[str, ...]:
        if self._lan_address_resolver is None:
            return ()
        try:
            return self._lan_address_resolver.resolve()
        except Exception as error:
            warnings.append(
                ScanWarning(
                    code="lan-address-lookup-failed",
                    message=f"Could not discover LAN addresses: {error}",
                )
            )
            return ()


def _listener_sort_key(listener: Listener) -> tuple[int, str, int, str]:
    """Keep output deterministic across operating-system scan ordering."""
    return (listener.port, listener.host, listener.pid or -1, listener.transport.value)


def _container_for_listener(
    listener: Listener, mappings: tuple[ContainerPortMapping, ...]
) -> ContainerInfo | None:
    """Match a socket to its Docker mapping, including wildcard host bindings."""
    for mapping in mappings:
        if mapping.port == listener.port and mapping.host == listener.host:
            return mapping.container
    for mapping in mappings:
        if mapping.port == listener.port and mapping.host in {"0.0.0.0", "::"}:
            return mapping.container
    return None


def _lan_urls(
    listener: Listener, health: HealthInfo | None, lan_addresses: tuple[str, ...]
) -> tuple[str, ...]:
    """Build LAN URLs only for HTTP listeners reachable beyond loopback."""
    if (
        health is None
        or health.protocol != "http"
    ):
        return ()
    if listener.host not in {"0.0.0.0", "::", *lan_addresses}:
        return ()
    return tuple(f"http://{address}:{listener.port}" for address in lan_addresses)
