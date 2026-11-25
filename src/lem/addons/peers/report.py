"""Look up the joined machines in parallel for the owner."""

import asyncio
import os

import httpx

from lem.addons.peers import commands, local, look, table, tailnet
from lem.kernel import paths
from lem.kernel.errors import Refusal


def listed() -> dict[str, tuple[commands.Answer, ...]]:
    """Read the checked table and look once for each board."""
    joined = table.read(paths.home(os.environ))
    return {"peers": asyncio.run(report(joined)) if joined else ()}


async def report(joined: dict[str, int]) -> tuple[commands.Answer, ...]:
    """A failure to look up the tailnet still shows the joined names."""
    try:
        space = local.status()
    except Refusal as error:
        return tuple(
            unavailable(name, port, error.why) for name, port in joined.items()
        )
    async with httpx.AsyncClient(timeout=look.LIST_TIMEOUT, trust_env=False) as client:
        return tuple(
            await asyncio.gather(
                *(
                    one(name, port, space.suffix, client)
                    for name, port in joined.items()
                ),
                return_exceptions=False,
            )
        )


async def one(
    name: str, port: int, suffix: str, client: httpx.AsyncClient
) -> commands.Answer:
    """A renamed or unreachable machine leaves the other rows intact."""
    try:
        base = tailnet.address(suffix, name, port)
    except Refusal as error:
        return unavailable(name, port, error.why)
    try:
        return await commands.probe(name, port, base, client)
    except Refusal as error:
        return unavailable(name, port, error.why, base)


def unavailable(name: str, port: int, why: str, base: str = "") -> commands.Answer:
    """Keep a failed peer's address and its reason when either can be read."""
    return commands.Answer(name=name, port=port, url=base, reachable=False, said=why)
