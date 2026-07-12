from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from portboard.adapters.http.httpx_probe import HttpxServiceProbe
from portboard.domain.models import HealthStatus, Listener


class _HealthyHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


def test_httpx_probe_checks_a_real_local_http_service() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HealthyHandler)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        health = HttpxServiceProbe().probe(
            Listener(host="127.0.0.1", port=server.server_port)
        )
    finally:
        server.shutdown()
        thread.join()
        server.server_close()

    assert health is not None
    assert health.status is HealthStatus.HEALTHY
    assert health.status_code == 200
