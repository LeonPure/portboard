from __future__ import annotations

import subprocess
import sys

from portboard import __version__


def test_python_module_exposes_a_stable_version_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "portboard", "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 0
    assert completed.stdout == f"portboard {__version__}\n"
    assert completed.stderr == ""
