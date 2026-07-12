from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from textual.widgets import DataTable, Input

from portboard.domain.models import Listener, ProcessInfo, ProjectInfo, Service, ServiceSnapshot
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
                ),
            ),
            warnings=(),
        )


def test_dashboard_filters_and_sorts_the_discovered_services() -> None:
    async def exercise() -> None:
        app = PortBoardApp(discover=FakeDiscoverServices(), refresh_interval=60)

        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one("#services", DataTable)
            assert table.row_count == 2
            assert table.get_row_at(0)[1] == "3000"

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
