"""psutil-backed guarded process termination."""

from __future__ import annotations

import shlex

import psutil

from portboard.domain.models import ProcessInfo


class PsutilProcessController:
    """Terminate a process only when its current metadata still matches."""

    def terminate_if_matches(self, expected: ProcessInfo) -> bool:
        """Revalidate PID metadata immediately before requesting termination."""
        if expected.create_time is None:
            return False
        try:
            process = psutil.Process(expected.pid)
            current = _process_info(process)
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            return False

        if not _matches_expected(current, expected):
            return False

        try:
            process.terminate()
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            return False
        return True


def _process_info(process: psutil.Process) -> ProcessInfo:
    """Read the identifying fields used for the final PID revalidation."""
    command_parts = process.cmdline()
    return ProcessInfo(
        pid=process.pid,
        name=process.name(),
        command=shlex.join(command_parts) if command_parts else None,
        cwd=process.cwd(),
        create_time=process.create_time(),
    )


def _matches_expected(current: ProcessInfo, expected: ProcessInfo) -> bool:
    """Compare every field that was readable when the service was discovered."""
    return (
        current.pid == expected.pid
        and current.create_time == expected.create_time
        and (expected.name is None or current.name == expected.name)
        and (expected.command is None or current.command == expected.command)
        and (expected.cwd is None or current.cwd == expected.cwd)
    )
