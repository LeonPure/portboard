"""Immutable, dependency-free models for a local-service snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Transport(StrEnum):
    """Network transports supported by the first discovery release."""

    TCP = "tcp"


class HealthStatus(StrEnum):
    """The availability state returned by a service health probe."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True, slots=True)
class Listener:
    """A local socket that is accepting connections."""

    host: str
    port: int
    transport: Transport = Transport.TCP
    pid: int | None = None


@dataclass(frozen=True, slots=True)
class ProcessInfo:
    """Best-effort process metadata associated with a listener."""

    pid: int
    name: str | None
    command: str | None
    cwd: str | None
    create_time: float | None = None


@dataclass(frozen=True, slots=True)
class ProjectInfo:
    """The Git project that contains a process working directory."""

    name: str
    root: str


@dataclass(frozen=True, slots=True)
class HealthInfo:
    """A successful HTTP response observed while checking a service."""

    protocol: str
    status: HealthStatus
    status_code: int
    latency_ms: float
    checked_at: datetime


@dataclass(frozen=True, slots=True)
class ContainerInfo:
    """A running Docker container that publishes a local TCP port."""

    id: str
    name: str
    image: str
    container_port: int


@dataclass(frozen=True, slots=True)
class ContainerPortMapping:
    """One Docker host-port mapping associated with a container."""

    host: str
    port: int
    container: ContainerInfo


@dataclass(frozen=True, slots=True)
class Service:
    """One discovered local service and the metadata available for it."""

    listener: Listener
    process: ProcessInfo | None = None
    project: ProjectInfo | None = None
    health: HealthInfo | None = None
    container: ContainerInfo | None = None
    lan_urls: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScanWarning:
    """A non-fatal issue encountered while producing a snapshot."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ListenerScan:
    """Listeners a system adapter could read, plus adapter-level warnings."""

    listeners: tuple[Listener, ...]
    warnings: tuple[ScanWarning, ...] = ()


@dataclass(frozen=True, slots=True)
class ContainerScan:
    """Docker port mappings visible to an optional container adapter."""

    mappings: tuple[ContainerPortMapping, ...]
    warnings: tuple[ScanWarning, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceSnapshot:
    """The complete result of one discovery operation."""

    observed_at: datetime
    services: tuple[Service, ...]
    warnings: tuple[ScanWarning, ...]
