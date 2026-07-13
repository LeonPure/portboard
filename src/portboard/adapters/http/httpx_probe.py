"""HTTPX-backed identification and health checking for TCP listeners."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter

import httpx

from portboard.domain.models import HealthInfo, HealthStatus, Listener

ClientFactory = Callable[[], httpx.Client]


class HttpxServiceProbe:
    """Issue a short HTTP request without treating non-HTTP ports as errors."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 0.5,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self._client_factory = client_factory or (
            lambda: httpx.Client(
                timeout=timeout_seconds,
                follow_redirects=False,
                trust_env=False,
            )
        )

    def probe(self, listener: Listener) -> HealthInfo | None:
        """Return health data for an HTTP response, otherwise no enrichment."""
        started_at = perf_counter()
        try:
            with self._client_factory() as client:
                response = client.get(
                    _url_for_listener(listener),
                    headers={"User-Agent": "portboard/0.0.0"},
                )
        except (httpx.HTTPError, OSError):
            return None

        latency_ms = (perf_counter() - started_at) * 1000
        return HealthInfo(
            protocol="http",
            status=(
                HealthStatus.HEALTHY
                if response.status_code < 400
                else HealthStatus.UNHEALTHY
            ),
            status_code=response.status_code,
            latency_ms=round(latency_ms, 3),
            checked_at=datetime.now(UTC),
        )


def _url_for_listener(listener: Listener) -> str:
    """Build a loopback-safe HTTP URL for a local listening endpoint."""
    host = listener.host
    if host == "0.0.0.0":
        host = "127.0.0.1"
    elif host == "::":
        host = "::1"

    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"http://{host}:{listener.port}/"
