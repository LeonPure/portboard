import json
from datetime import UTC, datetime

from portboard import cli
from portboard.cli import build_parser
from portboard.domain.models import ServiceSnapshot


def test_parser_uses_project_name() -> None:
    assert build_parser().prog == "portboard"


def test_parser_accepts_json_mode() -> None:
    assert build_parser().parse_args(["--json"]).json is True


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
