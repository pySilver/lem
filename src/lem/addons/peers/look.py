"""Look up a peer's board and keep its last valid answer."""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx
import msgspec

from lem.addons.peers.requests import HOP
from lem.addons.peers.rows import Row, gray, located
from lem.addons.peers.server import Server
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

SERVER_PATH = "/api/server"
WORKSPACES_PATH = "/api/workspaces"
# Bounds held by main's peer client (2026-11-25).
LIST_TIMEOUT = 4
LIST_FRESH = 5
JSON_CAP = 1_000_000

type Address = Callable[[str, int], Awaitable[str]]


class Seen(Frozen, frozen=True, kw_only=True):
    """The latest list, and when the peer last answered."""

    reachable: bool = False
    rows: tuple[Row, ...] = ()
    answered: int | None = None
    said: str = "no answer yet"


@dataclass(slots=True)
class Peer:
    """The last answer and the freshness of its attempt."""

    name: str
    port: int
    seen: Seen = field(default_factory=Seen)
    tried: float = float("-inf")
    pending: bool = False

    def failed(self, said: str) -> None:
        """Keep the previous answer and mark the machine unreachable."""
        self.tried = time.monotonic()
        self.seen = msgspec.structs.replace(self.seen, reachable=False, said=said)

    async def refresh(self, address: Address, client: httpx.AsyncClient) -> None:
        """Ask the list once when stale, even if several pages read it."""
        if self.pending or time.monotonic() - self.tried < LIST_FRESH:
            return
        self.pending = True
        try:
            self.seen = await self.look(address, client)
        except (httpx.HTTPError, Refusal, ValueError) as error:
            self.failed(str(error))
        finally:
            self.pending = False
            self.tried = time.monotonic()

    async def look(self, address: Address, client: httpx.AsyncClient) -> Seen:
        """The fresh rows and time of a valid reply."""
        base = await address(self.name, self.port)
        listed = await workspaces(base, self.name, client)
        answered = int(time.time() * 1000)
        return Seen(reachable=True, rows=listed, answered=answered, said="")

    def shown(self) -> tuple[Row, ...]:
        """The rows of a peer, including its last data when it cannot answer."""
        if self.seen.reachable:
            return self.seen.rows
        found = self.seen.rows or (Row(name="", host=self.name),)
        answered, said = self.seen.answered, self.seen.said
        return tuple(gray(row, answered, said) for row in found)


async def raw(client: httpx.AsyncClient, url: str) -> bytes:
    """Limit the size of the board JSON before decoding it."""
    async with client.stream("GET", url, headers={HOP: "1"}) as res:
        res.raise_for_status()
        body = bytearray()
        async for chunk in res.aiter_bytes():
            body.extend(chunk)
            if len(body) > JSON_CAP:
                raise ValueError("the peer's reply exceeds the board's JSON limit")
    return bytes(body)


async def workspaces(
    base: str, name: str, client: httpx.AsyncClient
) -> tuple[Row, ...]:
    """Ask for this machine's own workspaces only."""
    given = await raw(client, base + WORKSPACES_PATH)
    rows = decode(given, tuple[Row, ...])
    prefix = f"/{name}/"
    urls = (row.url for row in rows if row.url)
    if any(not url.startswith(prefix) for url in urls):
        raise ValueError("the peer serves its workspaces under another machine name")
    return tuple(located(row, name) for row in rows)


def decode[Shape](raw: bytes, shape: type[Shape]) -> Shape:
    """Report malformed or excessively nested JSON as a failed peer answer."""
    try:
        return msgspec.json.decode(raw, type=shape)
    except (msgspec.DecodeError, RecursionError) as error:
        raise ValueError("the peer gave no board JSON") from error


async def server(base: str, client: httpx.AsyncClient) -> Server:
    """Read a server's own name and install."""
    given = await raw(client, base + SERVER_PATH)
    return decode(given, Server)
