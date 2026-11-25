"""The life of the board server: its facts in `serve.json` while it runs, and beside it its
duties and the watcher of the board's notifications."""

from contextlib import asynccontextmanager
from functools import partial
from typing import TYPE_CHECKING

import anyio

from lem.board import facts as server_facts
from lem.board import serve_file
from lem.board.duties import runner

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from starlette.applications import Starlette
    from starlette.types import StatelessLifespan

    from lem.board.push.watch import Watcher


@asynccontextmanager
async def lived(
    app: Starlette, *, facts: server_facts.Facts, home: Path, watcher: Watcher
) -> AsyncIterator[None]:
    """The server's life: its facts in `serve.json`, its duties and the watcher of the
    board's notifications while it runs; at the stop each ends, and the file goes."""
    serve_file.write(home, facts)
    stopping = anyio.Event()
    async with anyio.create_task_group() as group:
        group.start_soon(runner.loop, home, stopping)
        group.start_soon(watcher.loop, stopping)
        inbox = getattr(app.state, "inbox_duty", None)
        if inbox is not None:
            group.start_soon(inbox, stopping)
        try:
            yield
        finally:
            stopping.set()
            await stopped(app)
    serve_file.remove(home, facts.pid)


async def stopped(app: Starlette) -> None:
    """Cancel the peer lookups that outlived their requests."""
    registry = getattr(app.state, "peer_registry", None)
    if registry is not None:
        await registry.stop()


def lifespan(
    facts: server_facts.Facts, home: Path, watcher: Watcher
) -> StatelessLifespan[Starlette]:
    """The life of the server `facts` of Lem's home folder `home`."""
    return partial(lived, facts=facts, home=home, watcher=watcher)
