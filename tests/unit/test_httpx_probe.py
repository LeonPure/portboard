from __future__ import annotations

import httpx

from portboard import __version__
from portboard.adapters.http.httpx_probe import HttpxServiceProbe
from portboard.domain.models import HealthStatus, Listener


def test_probe_reports_a_healthy_http_response_from_a_wildcard_listener() -> None:
    requested_urls: list[str] = []
    requested_user_agents: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        requested_user_agents.append(request.headers["User-Agent"])
        return httpx.Response(200)

    probe = HttpxServiceProbe(
        client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler))
    )

    health = probe.probe(Listener(host="0.0.0.0", port=8000))

    assert requested_urls == ["http://127.0.0.1:8000/"]
    assert requested_user_agents == [f"portboard/{__version__}"]
    assert health is not None
    assert health.status is HealthStatus.HEALTHY
    assert health.status_code == 200
    assert health.latency_ms >= 0


def test_probe_marks_server_errors_as_unhealthy() -> None:
    probe = HttpxServiceProbe(
        client_factory=lambda: httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(503))
        )
    )

    health = probe.probe(Listener(host="::1", port=3000))

    assert health is not None
    assert health.status is HealthStatus.UNHEALTHY
    assert health.status_code == 503


def test_probe_marks_client_errors_as_unhealthy() -> None:
    probe = HttpxServiceProbe(
        client_factory=lambda: httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(403))
        )
    )

    health = probe.probe(Listener(host="127.0.0.1", port=5000))

    assert health is not None
    assert health.status is HealthStatus.UNHEALTHY


def test_probe_ignores_non_http_or_unreachable_listeners() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    probe = HttpxServiceProbe(
        client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler))
    )

    assert probe.probe(Listener(host="127.0.0.1", port=5432)) is None
