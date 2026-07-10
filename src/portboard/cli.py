"""Command-line parsing and dispatch for PortBoard."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from portboard import __version__
from portboard.bootstrap import build_discover_services
from portboard.presentation.json_output import dumps


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the available command mode and return a process exit status."""
    parser = build_parser()
    arguments = parser.parse_args(argv)

    if not arguments.json:
        parser.print_help()
        return 0

    snapshot = build_discover_services().execute()
    sys.stdout.write(f"{dumps(snapshot)}\n")
    return 0
