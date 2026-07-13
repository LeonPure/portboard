from __future__ import annotations

import psutil

from portboard.adapters.system import process_controller
from portboard.adapters.system.process_controller import PsutilProcessController
from portboard.domain.models import ProcessInfo


class FakeProcess:
    pid = 123

    def __init__(self, *, command: list[str] | None = None) -> None:
        self._command = command or ["node", "server.js"]
        self.terminated = False

    def name(self) -> str:
        return "node"

    def cmdline(self) -> list[str]:
        return self._command

    def cwd(self) -> str:
        return "/code/web"

    def create_time(self) -> float:
        return 1000.0

    def terminate(self) -> None:
        self.terminated = True


def _expected(*, create_time: float | None = 1000.0) -> ProcessInfo:
    return ProcessInfo(123, "node", "node server.js", "/code/web", create_time)


def test_process_controller_terminates_only_after_metadata_matches(monkeypatch) -> None:
    process = FakeProcess()
    monkeypatch.setattr(process_controller.psutil, "Process", lambda pid: process)

    assert PsutilProcessController().terminate_if_matches(_expected()) is True
    assert process.terminated is True


def test_process_controller_refuses_a_pid_reused_by_a_different_command(monkeypatch) -> None:
    process = FakeProcess(command=["node", "other.js"])
    monkeypatch.setattr(process_controller.psutil, "Process", lambda pid: process)

    assert PsutilProcessController().terminate_if_matches(_expected()) is False
    assert process.terminated is False


def test_process_controller_refuses_a_process_without_a_known_start_time(
    monkeypatch,
) -> None:
    process = FakeProcess()
    monkeypatch.setattr(process_controller.psutil, "Process", lambda pid: process)

    assert (
        PsutilProcessController().terminate_if_matches(_expected(create_time=None))
        is False
    )
    assert process.terminated is False


def test_process_controller_degrades_when_process_access_is_denied(monkeypatch) -> None:
    def denied(pid: int):
        raise psutil.AccessDenied(pid=pid)

    monkeypatch.setattr(process_controller.psutil, "Process", denied)

    assert PsutilProcessController().terminate_if_matches(_expected()) is False
