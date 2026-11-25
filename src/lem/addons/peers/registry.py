"""The configured peers of one board server, and the last answer from each."""

import asyncio
from dataclasses import dataclass, field
from functools import partial
from typing import TYPE_CHECKING

import httpx

from lem.addons.peers import look, rows, table, tailnet
from lem.addons.peers.address import Address
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

# One shared wait for fresh answers, as on main (2026-11-25).
LIST_WAIT = 0.6


@dataclass(slots=True, kw_only=True)
class Registry:
    """A server's peer clients and their short-lived workspace cache."""

    home: Path
    own: str
    address: look.Address = field(default_factory=Address)
    transport: httpx.AsyncBaseTransport | None = None
    known: dict[str, look.Peer] = field(default_factory=dict)
    pending: dict[str, asyncio.Task[None]] = field(default_factory=dict)
    trouble: str | None = None

    def reload(self) -> dict[str, look.Peer]:
        """Reload the machine table and keep states whose names and ports did not change."""
        try:
            listed = table.read(self.home)
        except Refusal as error:
            self.trouble = error.why
            return {}
        self.trouble = None
        self.known = {
            name: kept(self.known.get(name), name, port)
            for name, port in listed.items()
            if name != self.own and name not in tailnet.RESERVED
        }
        return self.known

    async def spaces(self, own: tuple[rows.Row, ...]) -> tuple[rows.Row, ...]:
        """Ask the due peers in parallel and sort the resulting board links."""
        peers = self.reload()
        started = tuple(self.start(peer) for peer in peers.values())
        waiting = tuple(task for task in started if task is not None)
        if waiting:
            await asyncio.wait(waiting, timeout=LIST_WAIT)
        remote = tuple(row for peer in peers.values() for row in peer.shown())
        return rows.with_own(remote, own, self.own)

    def start(self, peer: look.Peer) -> asyncio.Task[None] | None:
        """Keep just one active look per peer, without waiting twice for an absent peer."""
        if peer.name in self.pending:
            return None
        task = asyncio.create_task(self.refresh(peer))
        self.pending[peer.name] = task
        task.add_done_callback(partial(self.completed, peer.name))
        return (
            task if peer.seen.reachable or peer.seen.said == "no answer yet" else None
        )

    async def refresh(self, peer: look.Peer) -> None:
        """Each background look owns its HTTP client."""
        async with self.client(look.LIST_TIMEOUT) as client:
            await peer.refresh(self.address, client)

    def completed(self, name: str, task: asyncio.Task[None]) -> None:
        """Release the pending row and report an unexpected task failure."""
        self.pending.pop(name, None)
        error = None if task.cancelled() else task.exception()
        if error is not None:
            peer = self.known.get(name)
            if peer:
                peer.failed(str(error))

    def client(self, timeout: float | httpx.Timeout) -> httpx.AsyncClient:
        """Use the tailnet directly, with certificate checks enabled."""
        return httpx.AsyncClient(
            transport=self.transport, timeout=timeout, trust_env=False
        )


def kept(old: look.Peer | None, name: str, port: int) -> look.Peer:
    """A changed port needs a new answer."""
    if old is not None and old.port == port:
        return old
    return look.Peer(name, port)
