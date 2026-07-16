import socket

import pytest

from portboard.adapters.system.psutil_scanner import PsutilListenerScanner


def test_system_scanner_returns_well_formed_listener_records() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener_socket:
        listener_socket.bind(("127.0.0.1", 0))
        listener_socket.listen()
        port = listener_socket.getsockname()[1]

        try:
            scan = PsutilListenerScanner().scan()
        except OSError as error:
            pytest.skip(f"operating system listener discovery is unavailable: {error}")

    assert any(listener.port == port for listener in scan.listeners)

    for listener in scan.listeners:
        assert listener.host
        assert 0 < listener.port < 65536
        assert listener.transport.value == "tcp"
