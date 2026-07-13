import pytest

from portboard.adapters.system.psutil_scanner import PsutilListenerScanner


def test_system_scanner_returns_well_formed_listener_records() -> None:
    try:
        scan = PsutilListenerScanner().scan()
    except OSError as error:
        pytest.skip(f"operating system listener discovery is unavailable: {error}")

    for listener in scan.listeners:
        assert listener.host
        assert 0 < listener.port < 65536
        assert listener.transport.value == "tcp"
