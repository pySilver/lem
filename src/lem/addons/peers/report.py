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
            commands.Answer(
                name=name, port=port, url="", reachable=False, said=error.why
            )
            for name, port in joined.items()
        )
    async with httpx.AsyncClient(timeout=look.LIST_TIMEOUT, trust_env=False) as client:
        return tuple(
            await asyncio.gather(
                *(
                    commands.probe(
                        name, port, tailnet.address(space.suffix, name, port), client
                    )
                    for name, port in joined.items()
                ),
                return_exceptions=False,
            )
        )
