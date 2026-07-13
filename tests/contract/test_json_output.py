from datetime import UTC, datetime

from portboard.domain.models import (
    ContainerInfo,
    HealthInfo,
    HealthStatus,
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
                health=HealthInfo(
                    protocol="http",
                    status=HealthStatus.HEALTHY,
                    status_code=200,
                    latency_ms=12.5,
                    checked_at=datetime(2026, 7, 12, 2, 0, tzinfo=UTC),
                ),
                container=ContainerInfo(
                    id="a762a2b37a1d",
                    name="example-web",
                    image="nginx:latest",
                    container_port=80,
                ),
                lan_urls=("http://192.168.1.20:3000",),
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
                "health": {
                    "protocol": "http",
                    "status": "healthy",
                    "status_code": 200,
                    "latency_ms": 12.5,
                    "checked_at": "2026-07-12T02:00:00Z",
                },
                "container": {
                    "id": "a762a2b37a1d",
                    "name": "example-web",
                    "image": "nginx:latest",
                    "container_port": 80,
                },
                "lan_urls": ["http://192.168.1.20:3000"],
            }
        ],
        "warnings": [{"code": "sample", "message": "A sample warning."}],
    }


def test_version_one_json_contract_preserves_unknown_values_as_null() -> None:
    snapshot = ServiceSnapshot(
        observed_at=datetime(2026, 7, 12, 2, 0, tzinfo=UTC),
        services=(Service(listener=Listener(host="127.0.0.1", port=5432)),),
        warnings=(),
    )

    service = snapshot_to_dict(snapshot)["services"][0]

    assert service == {
        "host": "127.0.0.1",
        "port": 5432,
        "transport": "tcp",
        "pid": None,
        "process_name": None,
        "command": None,
        "cwd": None,
        "project_root": None,
        "health": None,
        "container": None,
        "lan_urls": [],
    }
