from datetime import UTC, datetime

from portboard.application.actions import ServiceActions, service_url
from portboard.domain.models import (
    HealthInfo,
    HealthStatus,
    Listener,
    ProcessInfo,
    Service,
)


class FakeDesktop:
    def __init__(self) -> None:
        self.copied: list[str] = []
        self.opened: list[str] = []

    def copy_text(self, text: str) -> None:
        self.copied.append(text)

    def open_url(self, url: str) -> None:
        self.opened.append(url)


class FakeProcessController:
    def __init__(self, terminated: bool = True) -> None:
        self.terminated = terminated
        self.expected: ProcessInfo | None = None

    def terminate_if_matches(self, expected: ProcessInfo) -> bool:
        self.expected = expected
        return self.terminated


def _http_service() -> Service:
    return Service(
        listener=Listener(host="0.0.0.0", port=3000, pid=123),
        process=ProcessInfo(123, "node", "npm run dev", "/code/web", 1000.0),
        health=HealthInfo(
            protocol="http",
            status=HealthStatus.HEALTHY,
            status_code=200,
            latency_ms=3.2,
            checked_at=datetime(2026, 7, 12, tzinfo=UTC),
        ),
    )


def test_actions_open_and_copy_a_browser_safe_http_url() -> None:
    desktop = FakeDesktop()
    actions = ServiceActions(desktop, FakeProcessController())

    copy_result = actions.copy_url(_http_service())
    open_result = actions.open_url(_http_service())

    assert copy_result.succeeded is True
    assert open_result.succeeded is True
    assert desktop.copied == ["http://127.0.0.1:3000"]
    assert desktop.opened == ["http://127.0.0.1:3000"]


def test_actions_do_not_open_or_copy_a_non_http_listener() -> None:
    service = Service(listener=Listener(host="127.0.0.1", port=5432, pid=123))
    desktop = FakeDesktop()
    actions = ServiceActions(desktop, FakeProcessController())

    assert actions.copy_url(service).succeeded is False
    assert actions.open_url(service).succeeded is False
    assert desktop.copied == []
    assert desktop.opened == []
    assert service_url(service) is None


def test_actions_open_and_copy_an_identified_but_unhealthy_http_response() -> None:
    service = Service(
        listener=Listener(host="127.0.0.1", port=5000, pid=123),
        health=HealthInfo(
            protocol="http",
            status=HealthStatus.UNHEALTHY,
            status_code=403,
            latency_ms=1.0,
            checked_at=datetime(2026, 7, 12, tzinfo=UTC),
        ),
    )
    desktop = FakeDesktop()
    actions = ServiceActions(desktop, FakeProcessController())

    assert actions.copy_url(service).succeeded is True
    assert actions.open_url(service).succeeded is True
    assert desktop.copied == ["http://127.0.0.1:5000"]
    assert desktop.opened == ["http://127.0.0.1:5000"]


def test_stop_revalidates_the_discovered_process_before_termination() -> None:
    controller = FakeProcessController()
    service = _http_service()
    result = ServiceActions(FakeDesktop(), controller).stop(service)

    assert result.succeeded is True
    assert controller.expected == service.process


def test_stop_reports_a_changed_or_exited_process_without_termination() -> None:
    result = ServiceActions(FakeDesktop(), FakeProcessController(terminated=False)).stop(
        _http_service()
    )

    assert result.succeeded is False
    assert "revalidated" in result.message


def test_stop_refuses_a_process_without_a_stable_start_time() -> None:
    service = _http_service()
    service = Service(
        listener=service.listener,
        process=ProcessInfo(123, "node", "npm run dev", "/code/web"),
        health=service.health,
    )
    controller = FakeProcessController()

    result = ServiceActions(FakeDesktop(), controller).stop(service)

    assert result.succeeded is False
    assert "start time" in result.message
    assert controller.expected is None
