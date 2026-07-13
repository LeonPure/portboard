from __future__ import annotations

from datetime import UTC, datetime

from portboard.domain.models import Listener, ProjectInfo, Service, ServiceSnapshot
from portboard.presentation.tui.state import DashboardState


def test_dashboard_state_filters_and_reverses_sort_without_mutating_snapshot() -> None:
    snapshot = ServiceSnapshot(
        observed_at=datetime(2026, 7, 13, tzinfo=UTC),
        services=(
            Service(
                listener=Listener("127.0.0.1", 8000),
                project=ProjectInfo("api", "/code/api"),
            ),
            Service(
                listener=Listener("127.0.0.1", 3000),
                project=ProjectInfo("web", "/code/web"),
            ),
        ),
        warnings=(),
    )
    state = DashboardState(snapshot=snapshot)

    assert [service.listener.port for service in state.visible_services()] == [3000, 8000]

    state.set_filter("API")
    assert [service.listener.port for service in state.visible_services()] == [8000]

    state.set_filter("")
    state.toggle_sort("project")
    assert [service.project.name for service in state.visible_services()] == ["api", "web"]
    state.toggle_sort("project")
    assert [service.project.name for service in state.visible_services()] == ["web", "api"]
    assert snapshot.services[0].listener.port == 8000
