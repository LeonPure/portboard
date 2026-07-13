"""Command-line parsing and dispatch for PortBoard."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from portboard import __version__
from portboard.application.errors import DiscoveryUnavailable
from portboard.bootstrap import build_discover_services, build_service_actions
from portboard.presentation.json_output import dumps
from portboard.presentation.tui.app import PortBoardApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portboard",
        description="Discover local development services.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the discovered services as JSON",
    )
    parser.add_argument(
        "--refresh-seconds",
        type=_positive_refresh_seconds,
        metavar="SECONDS",
        help="automatically refresh the terminal dashboard at this interval",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the available command mode and return a process exit status."""
    parser = build_parser()
    arguments = parser.parse_args(argv)

    discover_services = build_discover_services()

    if arguments.json:
        try:
            snapshot = discover_services.execute()
        except DiscoveryUnavailable as error:
            sys.stderr.write(f"portboard: {error}\n")
            return 1
        sys.stdout.write(f"{dumps(snapshot)}\n")
        return 0

    PortBoardApp(
        discover=discover_services,
        actions=build_service_actions(),
        refresh_interval=arguments.refresh_seconds,
    ).run()
    return 0


def _positive_refresh_seconds(value: str) -> float:
    """Parse a refresh interval accepted by the live dashboard."""
    seconds = float(value)
    if seconds <= 0:
        raise argparse.ArgumentTypeError("refresh seconds must be greater than zero")
    return seconds
