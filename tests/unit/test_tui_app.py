from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from textual.widgets import Button, DataTable, Input

from portboard.domain.models import (
    HealthInfo,
    HealthStatus,
    Listener,
    ProcessInfo,
    ProjectInfo,
    Service,
    ServiceSnapshot,
)
from portboard.application.actions import ActionResult
from portboard.presentation.tui.app import PortBoardApp


class FakeDiscoverServices:
    def execute(self) -> ServiceSnapshot:
        return ServiceSnapshot(
            observed_at=datetime(2026, 7, 12, tzinfo=UTC),
            services=(
                Service(
                    listener=Listener(host="127.0.0.1", port=8000, pid=20),
                    process=ProcessInfo(20, "uvicorn", "uvicorn app:app", "/code/api"),
                    project=ProjectInfo("api", "/code/api"),
                ),
                Service(
                    listener=Listener(host="::1", port=3000, pid=10),
                    process=ProcessInfo(10, "node", "npm run dev", "/code/web"),
                    project=ProjectInfo("web", "/code/web"),
                    health=HealthInfo(
                        protocol="http",
                        status=HealthStatus.HEALTHY,
                        status_code=200,
                        latency_ms=3.2,
                        checked_at=datetime(2026, 7, 12, tzinfo=UTC),
                    ),
                ),
            ),
            warnings=(),
        )


class FakeActions:
    def __init__(self) -> None:
        self.copied: list[Service] = []
        self.opened: list[Service] = []
        self.stopped: list[Service] = []

    def copy_url(self, service: Service) -> ActionResult:
        self.copied.append(service)
        return ActionResult(True, "copied")

    def open_url(self, service: Service) -> ActionResult:
        self.opened.append(service)
        return ActionResult(True, "opened")

    def stop(self, service: Service) -> ActionResult:
        self.stopped.append(service)
        return ActionResult(True, "stopped")


def test_dashboard_filters_and_sorts_the_discovered_services() -> None:
    async def exercise() -> None:
        app = PortBoardApp(
            discover=FakeDiscoverServices(),
            actions=FakeActions(),
            refresh_interval=60,
        )

        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one("#services", DataTable)
            assert table.row_count == 2
            assert table.get_row_at(0)[1] == "3000"
            assert table.get_row_at(0)[2] == "healthy (200)"
            assert table.get_row_at(0)[5] == "http://[::1]:3000"

            filter_input = app.query_one("#filter", Input)
            filter_input.value = "uvicorn"
            await pilot.pause()
            assert table.row_count == 1
            assert table.get_row_at(0)[0] == "api"

            filter_input.value = ""
            await pilot.pause()
            app.action_sort_by_project()
            assert table.get_row_at(0)[0] == "api"
            app.action_sort_by_project()
            assert table.get_row_at(0)[0] == "web"

    asyncio.run(exercise())


def test_dashboard_routes_actions_through_confirmation_for_stopping() -> None:
    async def exercise() -> None:
        actions = FakeActions()
        app = PortBoardApp(
            discover=FakeDiscoverServices(),
            actions=actions,
            refresh_interval=60,
        )

        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_copy_url()
            app.action_open_url()
            assert len(actions.copied) == 1
            assert len(actions.opened) == 1

            app.action_request_stop()
            await pilot.pause()
            assert actions.stopped == []

            app.screen.query_one("#confirm-stop", Button).press()
            await pilot.pause()
            assert len(actions.stopped) == 1

    asyncio.run(exercise())
