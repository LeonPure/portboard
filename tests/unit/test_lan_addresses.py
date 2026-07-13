from __future__ import annotations

import socket
from types import SimpleNamespace

from portboard.adapters.system import lan_addresses
from portboard.adapters.system.lan_addresses import PsutilLanAddressResolver


def test_lan_address_resolver_keeps_only_usable_ipv4_addresses(monkeypatch) -> None:
    monkeypatch.setattr(
        lan_addresses.psutil,
        "net_if_addrs",
        lambda: {
            "lo0": [SimpleNamespace(family=socket.AF_INET, address="127.0.0.1")],
            "wifi": [
                SimpleNamespace(family=socket.AF_INET, address="192.168.1.20"),
                SimpleNamespace(family=socket.AF_INET, address="169.254.1.10"),
                SimpleNamespace(family=socket.AF_INET6, address="fe80::1"),
            ],
            "vpn": [SimpleNamespace(family=socket.AF_INET, address="10.0.0.4")],
        },
    )

    assert PsutilLanAddressResolver().resolve() == ("10.0.0.4", "192.168.1.20")
