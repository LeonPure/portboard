from datetime import UTC, datetime

from portboard.domain.models import (
    Listener,
    ProcessInfo,
    ProjectInfo,
    ScanWarning,
    Service,
    ServiceSnapshot,
)
from portboard.presentation.json_output import snapshot_to_dict


def test_version_one_json_contract() -> None:
    snapshot = ServiceSnapshot(
        observed_at=datetime(2026, 7, 12, 2, 0, tzinfo=UTC),
        services=(
            Service(
                listener=Listener(host="127.0.0.1", port=3000, pid=12345),
                process=ProcessInfo(
                    pid=12345,
                    name="node",
                    command="npm run dev",
                    cwd="/code/example",
                ),
                project=ProjectInfo(name="example", root="/code/example"),
            ),
        ),
        warnings=(ScanWarning(code="sample", message="A sample warning."),),
    )

    assert snapshot_to_dict(snapshot) == {
        "schema_version": 1,
        "observed_at": "2026-07-12T02:00:00Z",
        "services": [
            {
                "host": "127.0.0.1",
                "port": 3000,
                "transport": "tcp",
                "pid": 12345,
                "process_name": "node",
                "command": "npm run dev",
                "cwd": "/code/example",
                "project_root": "/code/example",
            }
        ],
        "warnings": [{"code": "sample", "message": "A sample warning."}],
    }
