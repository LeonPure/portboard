from __future__ import annotations

import subprocess

from portboard.adapters.containers import docker_cli
from portboard.adapters.containers.docker_cli import DockerCliScanner


def test_docker_scanner_reads_running_container_tcp_port_mappings(monkeypatch) -> None:
    responses = iter(
        (
            subprocess.CompletedProcess(["docker"], 0, stdout="abc123\n", stderr=""),
            subprocess.CompletedProcess(
                ["docker"],
                0,
                stdout="""[
                  {
                    "Id": "abc123",
                    "Name": "/example-api",
                    "Config": {"Image": "python:3.13"},
                    "NetworkSettings": {
                      "Ports": {
                        "8000/tcp": [{"HostIp": "0.0.0.0", "HostPort": "3000"}],
                        "53/udp": [{"HostIp": "0.0.0.0", "HostPort": "5353"}]
                      }
                    }
                  }
                ]""",
                stderr="",
            ),
        )
    )
    monkeypatch.setattr(docker_cli, "_run_docker", lambda arguments: next(responses))

    scan = DockerCliScanner().scan()

    assert len(scan.mappings) == 1
    mapping = scan.mappings[0]
    assert mapping.host == "0.0.0.0"
    assert mapping.port == 3000
    assert mapping.container.name == "example-api"
    assert mapping.container.container_port == 8000


def test_docker_scanner_silently_skips_a_missing_docker_cli(monkeypatch) -> None:
    def missing(arguments: list[str]):
        raise FileNotFoundError()

    monkeypatch.setattr(docker_cli, "_run_docker", missing)

    scan = DockerCliScanner().scan()

    assert scan.mappings == ()
    assert scan.warnings == ()


def test_docker_scanner_reports_an_unavailable_daemon_as_a_warning(monkeypatch) -> None:
    monkeypatch.setattr(
        docker_cli,
        "_run_docker",
        lambda arguments: subprocess.CompletedProcess(
            ["docker"], 1, stdout="", stderr="permission denied"
        ),
    )

    scan = DockerCliScanner().scan()

    assert scan.mappings == ()
    assert scan.warnings[0].code == "container-scan-failed"
