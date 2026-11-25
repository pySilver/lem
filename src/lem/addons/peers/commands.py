"""Join, leave, and report peers from the command line."""

import asyncio
import os
from typing import TYPE_CHECKING

import httpx

from lem.addons.peers import local, look, table, tailnet
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path


class Answer(Frozen, frozen=True, kw_only=True):
    """The owner sees the address and what the joined board answered."""

    name: str
    port: int
    url: str
    reachable: bool
    version: str | None = None
    workspaces: tuple[str, ...] = ()
    said: str = ""


async def probe(name: str, port: int, base: str, client: httpx.AsyncClient) -> Answer:
    """Ask the board once; a sleeping machine can still be joined."""
    try:
        return await inspected(name, port, base, client)
    except (httpx.HTTPError, ValueError) as error:
        said = str(error)
        return Answer(name=name, port=port, url=base, reachable=False, said=said)


async def inspected(
    name: str, port: int, base: str, client: httpx.AsyncClient
) -> Answer:
    """A reachable machine must serve under the name the owner joined."""
    found = await look.server(base, client)
    if found.host != name:
        raise Refusal(
            "peer-identity",
            f"{name} answers as {found.host}",
            "join the machine by its own name",
        )
    rows = await look.workspaces(base, name, client)
    return Answer(
        name=name,
        port=port,
        url=base,
        reachable=True,
        version=found.install.version,
        workspaces=tuple(row.name for row in rows),
    )


async def join(
    given: str, space: tailnet.Status, client: httpx.AsyncClient, home: Path
) -> Answer:
    """Validate the tailnet membership and update the machine's file."""
    from lem.settings.load import machine_of

    default = machine_of(home, os.environ).serve.tailscale_port
    name, port = tailnet.parse(given, space.suffix, default)
    tailnet.member(name, space)
    base = tailnet.address(space.suffix, name, port)
    seen = await probe(name, port, base, client)
    table.change(home, name, port)
    return seen


def joined(given: str) -> Answer:
    """Run the join command in a fresh HTTP session."""
    return asyncio.run(joining(given))


async def joining(given: str) -> Answer:
    """Open one client for the join probe."""
    home = paths.home(os.environ)
    async with httpx.AsyncClient(timeout=look.LIST_TIMEOUT, trust_env=False) as client:
        return await join(given, local.status(), client, home)


def leave(given: str) -> dict[str, object]:
    """Forget a peer without contacting it."""
    home = paths.home(os.environ)
    host = tailnet.named(given.partition(".")[0], "")
    remaining = table.change(home, host, None)
    return {"left": host, "peers": tuple(sorted(remaining))}
