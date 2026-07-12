"""Versioned JSON serialization for scripts and bug reports."""

from __future__ import annotations

import json
from datetime import UTC
from typing import Any

from portboard.domain.models import HealthInfo, Service, ServiceSnapshot

SCHEMA_VERSION = 1


def snapshot_to_dict(snapshot: ServiceSnapshot) -> dict[str, Any]:
    """Serialize a snapshot to the public JSON schema version 1."""
    observed_at = snapshot.observed_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": SCHEMA_VERSION,
        "observed_at": observed_at,
        "services": [_service_to_dict(service) for service in snapshot.services],
        "warnings": [
            {"code": warning.code, "message": warning.message}
            for warning in snapshot.warnings
        ],
    }


def dumps(snapshot: ServiceSnapshot) -> str:
    """Return human-readable, deterministic JSON without terminal formatting."""
    return json.dumps(snapshot_to_dict(snapshot), ensure_ascii=False, indent=2, sort_keys=True)


def _service_to_dict(service: Service) -> dict[str, Any]:
    process = service.process
    project = service.project
    return {
        "host": service.listener.host,
        "port": service.listener.port,
        "transport": service.listener.transport.value,
        "pid": process.pid if process is not None else service.listener.pid,
        "process_name": process.name if process is not None else None,
        "command": process.command if process is not None else None,
        "cwd": process.cwd if process is not None else None,
        "project_root": project.root if project is not None else None,
        "health": _health_to_dict(service.health),
    }


def _health_to_dict(health: HealthInfo | None) -> dict[str, Any] | None:
    """Serialize optional HTTP enrichment without changing core fields."""
    if health is None:
        return None
    checked_at = health.checked_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return {
        "protocol": health.protocol,
        "status": health.status.value,
        "status_code": health.status_code,
        "latency_ms": health.latency_ms,
        "checked_at": checked_at,
    }
