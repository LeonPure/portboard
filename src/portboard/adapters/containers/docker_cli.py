"""Docker CLI-backed running-container port discovery."""

from __future__ import annotations

import json
import subprocess

from portboard.domain.models import (
    ContainerInfo,
    ContainerPortMapping,
    ContainerScan,
    ScanWarning,
)


class DockerCliScanner:
    """Read published TCP ports from the optional local Docker CLI."""

    def scan(self) -> ContainerScan:
        """Return mappings without failing when Docker is not installed."""
        try:
            listed = _run_docker(["container", "ls", "--quiet"])
        except FileNotFoundError:
            return ContainerScan(mappings=())
        except (OSError, subprocess.TimeoutExpired) as error:
            return _failed_scan(error)

        if listed.returncode != 0:
            return _failed_scan(listed.stderr.strip() or "Docker CLI returned an error")

        container_ids = listed.stdout.split()
        if not container_ids:
            return ContainerScan(mappings=())

        try:
            inspected = _run_docker(["container", "inspect", *container_ids])
        except (OSError, subprocess.TimeoutExpired) as error:
            return _failed_scan(error)
        if inspected.returncode != 0:
            return _failed_scan(inspected.stderr.strip() or "Docker inspect returned an error")

        try:
            records = json.loads(inspected.stdout)
        except json.JSONDecodeError as error:
            return _failed_scan(f"Docker returned invalid JSON: {error}")
        return ContainerScan(mappings=_mappings_from_records(records))


def _run_docker(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    """Run Docker with a bounded timeout and text output."""
    return subprocess.run(
        ["docker", *arguments],
        capture_output=True,
        check=False,
        text=True,
        timeout=2,
    )


def _mappings_from_records(records: object) -> tuple[ContainerPortMapping, ...]:
    """Extract published TCP ports from Docker inspect JSON records."""
    if not isinstance(records, list):
        return ()

    mappings: list[ContainerPortMapping] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        ports = record.get("NetworkSettings", {}).get("Ports", {})
        if not isinstance(ports, dict):
            continue
        for container_endpoint, bindings in ports.items():
            container_port = _tcp_port(container_endpoint)
            if container_port is None or not isinstance(bindings, list):
                continue
            container = ContainerInfo(
                id=str(record.get("Id", "")),
                name=str(record.get("Name", "")).lstrip("/"),
                image=str(record.get("Config", {}).get("Image", "")),
                container_port=container_port,
            )
            for binding in bindings:
                if not isinstance(binding, dict):
                    continue
                try:
                    host_port = int(binding.get("HostPort", ""))
                except (TypeError, ValueError):
                    continue
                mappings.append(
                    ContainerPortMapping(
                        host=str(binding.get("HostIp") or "0.0.0.0"),
                        port=host_port,
                        container=container,
                    )
                )
    return tuple(mappings)


def _tcp_port(endpoint: object) -> int | None:
    """Parse a Docker endpoint such as ``8080/tcp``."""
    if not isinstance(endpoint, str) or not endpoint.endswith("/tcp"):
        return None
    try:
        return int(endpoint.removesuffix("/tcp"))
    except ValueError:
        return None


def _failed_scan(error: object) -> ContainerScan:
    return ContainerScan(
        mappings=(),
        warnings=(
            ScanWarning(
                code="container-scan-failed",
                message=f"Could not inspect Docker containers: {error}",
            ),
        ),
    )
