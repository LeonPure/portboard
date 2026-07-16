from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from threading import Event

from textual.widgets import Button, DataTable, Input, Static

from portboard.application.actions import ActionResult
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
from portboard.presentation.tui.app import (
    PortBoardApp,
    _qr_text,
    _refresh_status,
    _shortcut_footer_text,
    _truncate,
)


class FakeDiscoverServices:
    def execute(self) -> ServiceSnapshot:
        return ServiceSnapshot(
            observed_at=datetime(2026, 7, 12, tzinfo=UTC),
            services=(
                Service(
                    listener=Listener(host="127.0.0.1", port=8000, pid=20),
                    process=ProcessInfo(
                        20, "uvicorn", "uvicorn app:app", "/code/api", 1000.0
                    ),
                    project=ProjectInfo("api", "/code/api"),
                ),
                Service(
                    listener=Listener(host="::1", port=3000, pid=10),
                    process=ProcessInfo(
                        10, "node", "npm run dev", "/code/web", 2000.0
                    ),
                    project=ProjectInfo("web", "/code/web"),
                    health=HealthInfo(
                        protocol="http",
                        status=HealthStatus.HEALTHY,
                        status_code=200,
                        latency_ms=3.2,
                        checked_at=datetime(2026, 7, 12, tzinfo=UTC),
                    ),
                    container=ContainerInfo("abc123", "web", "node:22", 3000),
                    lan_urls=("http://192.168.1.20:3000",),
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
            assert table.get_row_at(0)[3] == "3.2 ms"
            assert table.get_row_at(0)[6] == "http://[::1]:3000"
            assert table.get_row_at(0)[7] == "web:3000"

            app.action_show_lan_qr()
            await pilot.pause()
            qr_screen = app.screen
            assert "██" in str(app.screen.query_one("#lan-qr-code", Static).render())
            await pilot.press("escape")
            await pilot.pause()
            assert app.screen is not qr_screen

            app.action_show_details()
            await pilot.pause()
            detail_text = str(
                app.screen.query_one("#service-detail-content", Static).render()
            )
            assert "Working directory: /code/web" in detail_text
            assert "Internal port: 3000" in detail_text
            assert "http://192.168.1.20:3000" in detail_text
            await pilot.press("escape")
            await pilot.pause()
            assert table.get_row_at(1)[3] == "—"

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


def test_qr_text_encodes_a_lan_url_as_a_visible_matrix() -> None:
    rendered = _qr_text("http://192.168.1.20:3000")

    assert any(block in rendered for block in ("█", "▀", "▄"))
    assert "\n" in rendered
    assert max(map(len, rendered.splitlines())) <= 80


def test_table_text_truncates_to_its_fixed_overview_width() -> None:
    assert _truncate("uvicorn app:app --reload", 12) == "uvicorn app…"


def test_shortcut_footer_renders_three_categorized_rows() -> None:
    assert _shortcut_footer_text().splitlines() == [
        "VIEW     r Refresh   f Filter   Esc Clear filter   d / Enter Details   w Warnings   q Quit  ",
        "SORT     p Project   o Port   n Process  ",
        "SERVICE  c Copy URL   b Open URL   x Stop process   l LAN QR  ",
    ]


def test_refresh_status_defaults_to_manual_and_describes_automatic_mode() -> None:
    assert _refresh_status(None) == "manual refresh (r)"
    assert _refresh_status(2.5) == "auto refresh every 2.5s"


def test_mouse_click_does_not_replace_the_keyboard_service_selection() -> None:
    async def exercise() -> None:
        app = PortBoardApp(
            discover=FakeDiscoverServices(),
            actions=FakeActions(),
            refresh_interval=60,
        )

        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one("#services", DataTable)
            assert table.cursor_row == 0

            await pilot.click(table, offset=(5, 2))
            await pilot.pause()

            assert table.cursor_row == 0

    asyncio.run(exercise())


def test_dashboard_shows_the_latest_scan_warnings() -> None:
    class WarningDiscoverServices(FakeDiscoverServices):
        def execute(self) -> ServiceSnapshot:
            snapshot = super().execute()
            return ServiceSnapshot(
                observed_at=snapshot.observed_at,
                services=snapshot.services,
                warnings=(
                    ScanWarning(
                        code="container-scan-failed",
                        message="Docker daemon is unavailable.",
                    ),
                ),
            )

    async def exercise() -> None:
        app = PortBoardApp(
            discover=WarningDiscoverServices(),
            actions=FakeActions(),
            refresh_interval=60,
        )

        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_show_warnings()
            await pilot.pause()

            warning_text = str(
                app.screen.query_one("#warnings-content", Static).render()
            )
            assert "container-scan-failed" in warning_text
            assert "Docker daemon is unavailable." in warning_text

    asyncio.run(exercise())


def test_refresh_runs_in_background_and_coalesces_repeated_requests() -> None:
    class BlockingDiscoverServices(FakeDiscoverServices):
        def __init__(self) -> None:
            self.started = Event()
            self.release = Event()
            self.calls = 0

        def execute(self) -> ServiceSnapshot:
            self.calls += 1
            if self.calls == 1:
                self.started.set()
                self.release.wait(timeout=2)
            return super().execute()

    async def exercise() -> None:
        discover = BlockingDiscoverServices()
        app = PortBoardApp(discover=discover, actions=FakeActions())

        async with app.run_test() as pilot:
            for _ in range(20):
                await pilot.pause()
                if discover.started.is_set():
                    break
            assert discover.started.is_set()
            table = app.query_one("#services", DataTable)
            assert app.query_one("#loading").display is True
            assert (
                str(app.query_one("#status", Static).render())
                == "Scanning local ports and checking services…"
            )

            app.action_focus_filter()
            await pilot.pause()
            assert app.query_one("#filter", Input).has_focus
            app.action_refresh()
            app.action_refresh()
            assert app._refresh_pending is True

            discover.release.set()
            for _ in range(40):
                await pilot.pause()
                if discover.calls == 2 and app._refresh_worker is None:
                    break

            assert discover.calls == 2
            assert app.query_one("#loading").display is False
            assert table.row_count == 2

    asyncio.run(exercise())


def test_refresh_completion_tolerates_an_unmounted_loading_banner() -> None:
    async def exercise() -> None:
        app = PortBoardApp(discover=FakeDiscoverServices(), actions=FakeActions())

        async with app.run_test() as pilot:
            await pilot.pause()
            await app.query_one("#loading").remove()

            app._set_initial_loading(False)

    asyncio.run(exercise())


def test_enter_opens_details_for_the_keyboard_selected_service() -> None:
    async def exercise() -> None:
        app = PortBoardApp(
            discover=FakeDiscoverServices(),
            actions=FakeActions(),
            refresh_interval=60,
        )

        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            assert "Service details" in str(
                app.screen.query_one("#service-detail-content", Static).render()
            )

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


def test_stop_confirmation_supports_keyboard_navigation_and_cancellation() -> None:
    async def exercise() -> None:
        actions = FakeActions()
        app = PortBoardApp(
            discover=FakeDiscoverServices(),
            actions=actions,
            refresh_interval=60,
        )

        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_request_stop()
            await pilot.pause()
            cancel_button = app.screen.query_one("#cancel-stop", Button)
            process_details = app.screen.query_one("#stop-process", Static)
            assert cancel_button.flat is True
            assert app.focused is cancel_button
            assert process_details.size.height >= 3
            assert "Command   npm run dev" in str(process_details.render())

            await pilot.press("right")
            assert app.focused is app.screen.query_one("#confirm-stop", Button)
            await pilot.press("enter")
            await pilot.pause()
            assert len(actions.stopped) == 1

            app.action_request_stop()
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert len(actions.stopped) == 1

    asyncio.run(exercise())
