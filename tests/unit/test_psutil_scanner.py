from __future__ import annotations

import psutil

from portboard.adapters.system.psutil_scanner import PsutilListenerScanner


def test_scanner_reports_a_warning_when_global_scan_is_not_permitted(monkeypatch) -> None:
    def reject_global_scan(*args, **kwargs):
        raise psutil.AccessDenied(pid=1)

    monkeypatch.setattr(psutil, "net_connections", reject_global_scan)
    monkeypatch.setattr(psutil, "process_iter", lambda: [])

    scan = PsutilListenerScanner().scan()

    assert scan.listeners == ()
    assert scan.warnings[0].code == "system-scan-partial"
