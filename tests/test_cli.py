import json
from datetime import UTC, datetime

from portboard import cli
from portboard.cli import build_parser
from portboard.domain.models import ServiceSnapshot


def test_parser_uses_project_name() -> None:
    assert build_parser().prog == "portboard"


def test_parser_accepts_json_mode() -> None:
    assert build_parser().parse_args(["--json"]).json is True


def test_parser_rejects_non_positive_refresh_interval() -> None:
    parser = build_parser()

    try:
        parser.parse_args(["--refresh-seconds", "0"])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("expected a parsing failure")


def test_json_mode_prints_a_snapshot(monkeypatch, capsys) -> None:
    class FakeDiscoverServices:
        def execute(self) -> ServiceSnapshot:
            return ServiceSnapshot(
                observed_at=datetime(2026, 7, 12, tzinfo=UTC),
                services=(),
                warnings=(),
            )

    monkeypatch.setattr(cli, "build_discover_services", FakeDiscoverServices)

    assert cli.main(["--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "observed_at": "2026-07-12T00:00:00Z",
        "schema_version": 1,
        "services": [],
        "warnings": [],
    }


def test_default_mode_runs_the_terminal_dashboard(monkeypatch) -> None:
    discovered = object()
    created: dict[str, object] = {}

    class FakeDashboard:
        def __init__(self, *, discover, actions, refresh_interval: float) -> None:
            created["discover"] = discover
            created["actions"] = actions
            created["refresh_interval"] = refresh_interval

        def run(self) -> None:
            created["ran"] = True

    monkeypatch.setattr(cli, "build_discover_services", lambda: discovered)
    monkeypatch.setattr(cli, "build_service_actions", lambda: "actions")
    monkeypatch.setattr(cli, "PortBoardApp", FakeDashboard)

    assert cli.main([]) == 0
    assert created == {
        "discover": discovered,
        "actions": "actions",
        "refresh_interval": 3.0,
        "ran": True,
    }
