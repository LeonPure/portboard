from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from time import sleep

import pytest

from portboard.application.discover import DiscoverServices
from portboard.application.errors import DiscoveryUnavailable
from portboard.domain.models import (
    ContainerInfo,
    ContainerPortMapping,
    ContainerScan,
    HealthInfo,
    HealthStatus,
    Listener,
    ListenerScan,
    ProcessInfo,
    ProjectInfo,
)


class FakeScanner:
    def __init__(self) -> None:
        self.listeners = (
            Listener(host="127.0.0.1", port=8000, pid=20),
            Listener(host="127.0.0.1", port=3000, pid=10),
            Listener(host="::1", port=9000, pid=None),
        )
        self.processes = {
            10: ProcessInfo(
                pid=10,
                name="node",
                command="npm run dev",
                cwd="/workspace/web",
            ),
            20: ProcessInfo(
                pid=20,
                name="uvicorn",
                command="uvicorn app:app",
                cwd="/workspace/api",
            ),
        }

    def scan(self) -> ListenerScan:
        return ListenerScan(listeners=self.listeners)

    def get_process(self, pid: int) -> ProcessInfo | None:
        return self.processes.get(pid)


class FakeProjectResolver:
    def resolve(self, cwd: str) -> ProjectInfo | None:
        return ProjectInfo(name=cwd.rsplit("/", 1)[-1], root=cwd)


def test_discovery_sorts_services_and_keeps_partial_results() -> None:
    discover = DiscoverServices(
        scanner=FakeScanner(),
        project_resolver=FakeProjectResolver(),
        clock=lambda: datetime(2026, 7, 12, tzinfo=UTC),
    )

    snapshot = discover.execute()

    assert [service.listener.port for service in snapshot.services] == [3000, 8000, 9000]
    assert snapshot.services[0].project == ProjectInfo(name="web", root="/workspace/web")
    assert snapshot.services[2].process is None
    assert snapshot.warnings[0].code == "process-unavailable"


def test_discovery_turns_project_failures_into_warnings() -> None:
    class BrokenProjectResolver:
        def resolve(self, cwd: str) -> ProjectInfo | None:
            raise OSError("repository temporarily unavailable")

    snapshot = DiscoverServices(
        scanner=FakeScanner(),
        project_resolver=BrokenProjectResolver(),
    ).execute()

    assert len(snapshot.services) == 3
    assert [warning.code for warning in snapshot.warnings] == [
        "project-lookup-failed",
        "project-lookup-failed",
        "process-unavailable",
    ]


def test_discovery_enriches_a_service_with_http_health() -> None:
    health = HealthInfo(
        protocol="http",
        status=HealthStatus.HEALTHY,
        status_code=200,
        latency_ms=4.2,
        checked_at=datetime(2026, 7, 12, tzinfo=UTC),
    )

    class FakeProbe:
        def probe(self, listener: Listener) -> HealthInfo | None:
            return health if listener.port == 3000 else None

    snapshot = DiscoverServices(
        scanner=FakeScanner(),
        project_resolver=FakeProjectResolver(),
        service_probe=FakeProbe(),
    ).execute()

    assert snapshot.services[0].health == health


def test_discovery_turns_probe_failures_into_warnings() -> None:
    class BrokenProbe:
        def probe(self, listener: Listener) -> HealthInfo | None:
            raise OSError("probe temporarily unavailable")

    snapshot = DiscoverServices(
        scanner=FakeScanner(),
        project_resolver=FakeProjectResolver(),
        service_probe=BrokenProbe(),
    ).execute()

    assert all(service.health is None for service in snapshot.services)
    assert [warning.code for warning in snapshot.warnings].count("health-probe-failed") == 3


def test_discovery_probes_services_with_bounded_concurrency() -> None:
    class ConcurrentProbe:
        def __init__(self) -> None:
            self.active = 0
            self.maximum_active = 0
            self.lock = Lock()

        def probe(self, listener: Listener) -> HealthInfo | None:
            with self.lock:
                self.active += 1
                self.maximum_active = max(self.maximum_active, self.active)
            sleep(0.02)
            with self.lock:
                self.active -= 1
            return None

    probe = ConcurrentProbe()
    DiscoverServices(
        scanner=FakeScanner(),
        project_resolver=FakeProjectResolver(),
        service_probe=probe,
        probe_workers=2,
    ).execute()

    assert probe.maximum_active == 2


def test_discovery_attaches_a_matching_docker_container() -> None:
    container = ContainerInfo("abc123", "api", "python:3.13", 8000)

    class FakeContainerScanner:
        def scan(self) -> ContainerScan:
            return ContainerScan(
                mappings=(
                    ContainerPortMapping(host="0.0.0.0", port=3000, container=container),
                )
            )

    snapshot = DiscoverServices(
        scanner=FakeScanner(),
        project_resolver=FakeProjectResolver(),
        container_scanner=FakeContainerScanner(),
    ).execute()

    assert snapshot.services[0].container == container


def test_discovery_preserves_services_when_container_scanning_fails() -> None:
    class BrokenContainerScanner:
        def scan(self) -> ContainerScan:
            raise OSError("Docker daemon unavailable")

    snapshot = DiscoverServices(
        scanner=FakeScanner(),
        project_resolver=FakeProjectResolver(),
        container_scanner=BrokenContainerScanner(),
    ).execute()

    assert len(snapshot.services) == 3
    assert snapshot.warnings[0].code == "container-scan-failed"


def test_discovery_builds_lan_urls_for_wildcard_http_listeners() -> None:
    health = HealthInfo(
        protocol="http",
        status=HealthStatus.HEALTHY,
        status_code=200,
        latency_ms=1.2,
        checked_at=datetime(2026, 7, 12, tzinfo=UTC),
    )

    class FakeProbe:
        def probe(self, listener: Listener) -> HealthInfo | None:
            return health

    class FakeLanResolver:
        def resolve(self) -> tuple[str, ...]:
            return ("192.168.1.20",)

    scanner = FakeScanner()
    scanner.listeners = (Listener(host="0.0.0.0", port=3000, pid=10),)
    snapshot = DiscoverServices(
        scanner=scanner,
        project_resolver=FakeProjectResolver(),
        service_probe=FakeProbe(),
        lan_address_resolver=FakeLanResolver(),
    ).execute()

    assert snapshot.services[0].lan_urls == ("http://192.168.1.20:3000",)


def test_discovery_builds_lan_urls_for_identified_unhealthy_http_services() -> None:
    health = HealthInfo(
        protocol="http",
        status=HealthStatus.UNHEALTHY,
        status_code=404,
        latency_ms=1.2,
        checked_at=datetime(2026, 7, 12, tzinfo=UTC),
    )

    class FakeProbe:
        def probe(self, listener: Listener) -> HealthInfo | None:
            return health

    class FakeLanResolver:
        def resolve(self) -> tuple[str, ...]:
            return ("192.168.1.20",)

    scanner = FakeScanner()
    scanner.listeners = (Listener(host="0.0.0.0", port=3000, pid=10),)
    snapshot = DiscoverServices(
        scanner=scanner,
        project_resolver=FakeProjectResolver(),
        service_probe=FakeProbe(),
        lan_address_resolver=FakeLanResolver(),
    ).execute()

    assert snapshot.services[0].lan_urls == ("http://192.168.1.20:3000",)


def test_discovery_raises_a_clear_error_when_base_scanning_fails() -> None:
    class BrokenScanner(FakeScanner):
        def scan(self) -> ListenerScan:
            raise PermissionError("not permitted")

    with pytest.raises(DiscoveryUnavailable, match="Could not scan local TCP listeners"):
        DiscoverServices(
            scanner=BrokenScanner(),
            project_resolver=FakeProjectResolver(),
        ).execute()
