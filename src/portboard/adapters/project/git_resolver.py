"""Git CLI-backed project resolution."""

from __future__ import annotations

from pathlib import Path
import subprocess

from portboard.domain.models import ProjectInfo


class GitProjectResolver:
    """Find the nearest Git repository containing a working directory."""

    def resolve(self, cwd: str) -> ProjectInfo | None:
        try:
            completed = subprocess.run(
                ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                capture_output=True,
                check=False,
                text=True,
                timeout=1,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return None

        if completed.returncode != 0:
            return None

        root = completed.stdout.strip()
        if not root:
            return None

        root_path = Path(root)
        return ProjectInfo(name=root_path.name, root=str(root_path))
