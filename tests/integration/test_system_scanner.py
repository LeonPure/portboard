from portboard.adapters.system.psutil_scanner import PsutilListenerScanner


def test_system_scanner_returns_well_formed_listener_records() -> None:
    scan = PsutilListenerScanner().scan()

    for listener in scan.listeners:
        assert listener.host
        assert 0 < listener.port < 65536
        assert listener.transport.value == "tcp"
