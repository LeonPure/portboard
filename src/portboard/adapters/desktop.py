"""Desktop integrations for browser and clipboard actions."""

from __future__ import annotations

import shutil
import subprocess
import sys
import webbrowser


class SystemDesktopController:
    """Use standard macOS and Linux desktop tools when they are available."""

    def open_url(self, url: str) -> None:
        """Open a URL in the configured default browser."""
        if not webbrowser.open(url, new=2):
            raise RuntimeError("the default browser did not accept the URL")

    def copy_text(self, text: str) -> None:
        """Copy text using the platform's clipboard command."""
        command = _clipboard_command()
        subprocess.run(command, input=text, text=True, check=True)


def _clipboard_command() -> list[str]:
    """Return the first supported clipboard command for macOS or Linux."""
    if sys.platform == "darwin":
        return ["pbcopy"]
    if shutil.which("wl-copy"):
        return ["wl-copy"]
    if shutil.which("xclip"):
        return ["xclip", "-selection", "clipboard"]
    raise RuntimeError("no supported clipboard command was found")
