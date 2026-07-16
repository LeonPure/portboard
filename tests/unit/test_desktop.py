from __future__ import annotations

import subprocess

from portboard.adapters import desktop
from portboard.adapters.desktop import SystemDesktopController


def test_desktop_opens_a_url_in_a_new_browser_tab(monkeypatch) -> None:
    opened: list[tuple[str, int]] = []

    def open_url(url: str, new: int) -> bool:
        opened.append((url, new))
        return True

    monkeypatch.setattr(desktop.webbrowser, "open", open_url)

    SystemDesktopController().open_url("http://127.0.0.1:3000")

    assert opened == [("http://127.0.0.1:3000", 2)]


def test_desktop_copies_text_with_the_platform_clipboard_command(monkeypatch) -> None:
    calls: list[tuple[list[str], str, bool, bool]] = []
    monkeypatch.setattr(desktop.sys, "platform", "darwin")

    def run(command, *, input, text, check):
        calls.append((command, input, text, check))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(desktop.subprocess, "run", run)

    SystemDesktopController().copy_text("http://127.0.0.1:3000")

    assert calls == [(["pbcopy"], "http://127.0.0.1:3000", True, True)]


def test_desktop_uses_the_native_windows_clipboard_command(monkeypatch) -> None:
    calls: list[tuple[list[str], str, bool, bool]] = []
    monkeypatch.setattr(desktop.sys, "platform", "win32")

    def run(command, *, input, text, check):
        calls.append((command, input, text, check))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(desktop.subprocess, "run", run)

    SystemDesktopController().copy_text("http://127.0.0.1:3000")

    assert calls == [(["clip.exe"], "http://127.0.0.1:3000", True, True)]


def test_desktop_reports_when_the_browser_rejects_a_url(monkeypatch) -> None:
    monkeypatch.setattr(desktop.webbrowser, "open", lambda url, new: False)

    try:
        SystemDesktopController().open_url("http://127.0.0.1:3000")
    except RuntimeError as error:
        assert "browser" in str(error)
    else:
        raise AssertionError("expected browser failure")
