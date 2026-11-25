"""The address of a board listener, for the commands that ask it who serves."""

from contextlib import suppress
from ipaddress import IPv4Address
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from lem.board import client, heard, machine, serve_file

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.board.facts import Facts

type Address = tuple[str, int]


def local(host: str) -> str:
    """A wildcard listener is reached on the loopback of its own address family."""
    if host == "::":
        return "::1"
    if host == str(IPv4Address(0)):
        return client.LOOPBACK
    return host


def recorded(home: Path, environ: Mapping[str, str]) -> Address | None:
    """The listener of this home folder in its record, if this call may ask its port."""
    named = serve_file.read(home)
    if (
        named is None
        or named.home != str(home)
        or not machine.allowed(named.port, environ)
    ):
        return None
    with suppress(ValueError):
        host = urlsplit(named.url).hostname
        if host is not None:
            return local(host), named.port
    return None


def alternate(
    home: Path, environ: Mapping[str, str], port: int
) -> Facts | heard.Other | None:
    """Ask a recorded nondefault listener on the configured port before the default."""
    named = recorded(home, environ)
    if named is None:
        return None
    host, recorded_port = named
    if recorded_port == port and host != client.LOOPBACK:
        with suppress(heard.Unrelated):
            return client.ask(port, home, host)
    return None
