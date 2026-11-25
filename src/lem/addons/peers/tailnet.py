"""Tailscale names and the addresses of boards on the same tailnet."""

import re

from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings.machine import HIGHEST_PORT

PORT_DIGITS = len(str(HIGHEST_PORT))
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
# The route words reserved by the board, apart from the machine's own name.
RESERVED = frozenset(("api", "assets", "push", "manifest.webmanifest", "sw.js"))


class Machine(Frozen, frozen=True, kw_only=True, rename={"dns": "DNSName"}):
    """One machine name from Tailscale."""

    dns: str = ""

    def label(self) -> str:
        """The short label as Tailscale names it."""
        return self.dns.partition(".")[0].lower()


class Status(
    Frozen,
    frozen=True,
    kw_only=True,
    rename={"suffix": "MagicDNSSuffix", "own": "Self", "peers": "Peer"},
):
    """The names that Tailscale status reports to this machine."""

    suffix: str = ""
    own: Machine | None = None
    peers: dict[str, Machine] | None = None


def named(word: str, suffix: str) -> str:
    """Accept one DNS label or a DNS name of this tailnet."""
    written = word.strip().lower().rstrip(".")
    name, dot, domain = written.partition(".")
    local = suffix.lower().rstrip(".")
    if not LABEL.fullmatch(name) or (dot and domain != local):
        raise Refusal(
            "peer-name",
            f"{word!r} is no machine's name on the owner's tailnet",
            "use the machine name from tailscale status",
        )
    return name


def parse(word: str, suffix: str, default_port: int) -> tuple[str, int]:
    """The name and its explicit port, or the door's port from settings."""
    host, separator, port = word.partition(":")
    number = parsed_port(port) if separator else default_port
    return named(host, suffix), number


def address(suffix: str, host: str, port: int) -> str:
    """A joined machine's HTTPS address on the owner's tailnet."""
    domain = suffix.lower().rstrip(".")
    if not all(map(LABEL.fullmatch, domain.split("."))):
        raise Refusal(
            "tailnet", "Tailscale supplied no valid DNS suffix", "connect to Tailscale"
        )
    return f"https://{host}.{domain}:{port}"


def parsed_port(port: str) -> int:
    """Read an ASCII port inside the TCP range."""
    if port.isascii() and port.isdecimal() and len(port) <= PORT_DIGITS:
        number = int(port)
        if 1 <= number <= HIGHEST_PORT:
            return number
    raise Refusal("peer-port", f"{port!r} is no port", "use a port from 1 to 65535")


def member(host: str, space: Status) -> None:
    """Only another named machine of this tailnet may join."""
    own = space.own.label() if space.own else ""
    peers = space.peers or {}
    names = {peer.label() for peer in peers.values()}
    if host == own or host in RESERVED or host not in names:
        raise Refusal(
            "peer-member",
            f"{host!r} is no other board on the owner's tailnet",
            "choose another machine from tailscale status",
        )
