"""Pure formatting helpers shared by PortBoard's terminal widgets and screens."""

from __future__ import annotations

from collections.abc import Iterable

import qrcode

from portboard.domain.models import HealthStatus, ScanWarning, Service


def searchable_text(service: Service) -> str:
    """Return user-facing service fields that should match the filter."""
    return " ".join(
        value
        for value in (
            service.listener.host,
            str(service.listener.port),
            service.process.name if service.process else None,
            service.process.command if service.process else None,
            service.process.cwd if service.process else None,
            service.project.name if service.project else None,
            service.project.root if service.project else None,
        )
        if value is not None
    )


def sort_key(service: Service, field: str) -> tuple[str, int]:
    """Return a deterministic key for each supported user sort."""
    if field == "port":
        return ("", service.listener.port)
    if field == "project":
        return (
            service.project.name.casefold() if service.project else "",
            service.listener.port,
        )
    return (
        service.process.name.casefold()
        if service.process and service.process.name
        else "",
        service.listener.port,
    )


def endpoint(service: Service) -> str:
    """Format a TCP endpoint, including a URL whenever HTTP was identified."""
    host = service.listener.host
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    endpoint_value = f"{host}:{service.listener.port}"
    return (
        f"http://{endpoint_value}"
        if service.health and service.health.protocol == "http"
        else endpoint_value
    )


def status(service: Service) -> str:
    """Render the best available service status without inventing HTTP health."""
    if service.health is None:
        return "listening"
    label = (
        "healthy" if service.health.status is HealthStatus.HEALTHY else "unhealthy"
    )
    return f"{label} ({service.health.status_code})"


def latency(service: Service) -> str:
    """Render HTTP probe latency only when a service responded to the probe."""
    if service.health is None:
        return "—"
    return f"{service.health.latency_ms:.1f} ms"


def refresh_status(refresh_interval: float | None) -> str:
    """Describe whether a snapshot needs manual refresh or is periodically updated."""
    if refresh_interval is None:
        return "manual refresh (r)"
    return f"auto refresh every {refresh_interval:g}s"


def container_label(service: Service) -> str:
    """Render a compact Docker label when a port mapping was found."""
    if service.container is None:
        return "—"
    return f"{service.container.name}:{service.container.container_port}"


def truncate(value: str, width: int) -> str:
    """Fit a table cell into its fixed overview width without horizontal scroll."""
    return value if len(value) <= width else f"{value[: width - 1]}…"


def service_key(service: Service) -> str:
    """Create a stable table key for the lifetime of one snapshot."""
    return f"{service.listener.host}:{service.listener.port}:{service.listener.pid}"


def service_details(service: Service) -> str:
    """Format complete service metadata for a readable, non-truncated modal."""
    process = service.process
    project = service.project
    health = service.health
    container = service.container
    lan_urls = "\n".join(f"  - {url}" for url in service.lan_urls) or "  - —"
    health_lines = (
        "  - —"
        if health is None
        else "\n".join(
            (
                f"  - Protocol: {health.protocol}",
                f"  - Status: {health.status.value} ({health.status_code})",
                f"  - Latency: {health.latency_ms:.1f} ms",
                f"  - Checked: {health.checked_at.isoformat()}",
            )
        )
    )
    container_lines = (
        "  - —"
        if container is None
        else "\n".join(
            (
                f"  - Name: {container.name}",
                f"  - Image: {container.image}",
                f"  - ID: {container.id}",
                f"  - Internal port: {container.container_port}",
            )
        )
    )
    return "\n".join(
        (
            "Service details",
            "",
            "Listener",
            f"  - Address: {service.listener.host}:{service.listener.port}",
            f"  - Transport: {service.listener.transport.value}",
            f"  - PID: {service.listener.pid if service.listener.pid is not None else '—'}",
            "",
            "Process",
            f"  - Name: {process.name if process and process.name else '—'}",
            f"  - Command: {process.command if process and process.command else '—'}",
            f"  - Working directory: {process.cwd if process and process.cwd else '—'}",
            "",
            "Project",
            f"  - Name: {project.name if project else '—'}",
            f"  - Root: {project.root if project else '—'}",
            "",
            "Health",
            health_lines,
            "",
            "Container",
            container_lines,
            "",
            "LAN URLs",
            lan_urls,
        )
    )


def warnings_details(warnings: Iterable[ScanWarning]) -> str:
    """Format snapshot warnings for a scrollable diagnostics screen."""
    warning_lines = tuple(warnings)
    return "\n\n".join(
        f"{index}. {warning.code}\n   {warning.message}"
        for index, warning in enumerate(warning_lines, start=1)
    )


def qr_text(url: str) -> str:
    """Encode a URL as a compact terminal QR code using Unicode half blocks."""
    qr = qrcode.QRCode(border=1)
    qr.add_data(url, optimize=0)
    qr.make(fit=True)
    rows = qr.get_matrix()
    if len(rows) % 2:
        rows.append([False] * len(rows[0]))
    return "\n".join(
        "".join(_half_block(top, bottom) for top, bottom in zip(upper, lower))
        for upper, lower in zip(rows[::2], rows[1::2])
    )


def _half_block(top: bool, bottom: bool) -> str:
    if top and bottom:
        return "█"
    if top:
        return "▀"
    if bottom:
        return "▄"
    return " "
