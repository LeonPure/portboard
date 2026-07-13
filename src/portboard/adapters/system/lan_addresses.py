"""psutil-backed local network address discovery."""

from __future__ import annotations

import ipaddress
import socket

import psutil


class PsutilLanAddressResolver:
    """Return usable local IPv4 addresses without choosing an external route."""

    def resolve(self) -> tuple[str, ...]:
        """Read active interface addresses with no network side effects."""
        addresses: set[str] = set()
        for interface_addresses in psutil.net_if_addrs().values():
            for address in interface_addresses:
                if address.family != socket.AF_INET:
                    continue
                candidate = ipaddress.ip_address(address.address)
                if (
                    candidate.is_loopback
                    or candidate.is_link_local
                    or candidate.is_multicast
                    or candidate.is_unspecified
                ):
                    continue
                addresses.add(str(candidate))
        return tuple(sorted(addresses, key=lambda address: tuple(map(int, address.split(".")))))
