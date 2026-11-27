"""The life of the board server: its facts in `serve.json` while it runs, and beside it its
loops (`turns.py`), none of whose failures ends it: the duties, the watcher of the board's
notifications, the look at its own install (`handover.py`), and the Inbox's when it is on.
"""

from contextlib import asynccontextmanager
from functools import partial
from typing import TYPE_CHECKING

import anyio

from lem.board import facts as server_facts
from lem.board import handover, serve_file, turns, update
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
    """The server's life: its facts in `serve.json` and its release in the update record,
    its loops while it runs; at the stop each ends, and the file goes."""
    recorded(home, facts)
    stopping = anyio.Event()
    async with anyio.create_task_group() as group:
        for turn in turns_of(app, home, watcher):
            group.start_soon(turns.kept_up, turn, stopping)
        try:
            yield
        finally:
            stopping.set()
            await stopped(app)
    serve_file.remove(home, facts.pid)


def turns_of(app: Starlette, home: Path, watcher: Watcher) -> list[turns.Turn]:
    """The loops of the server's life; the look at its install is the app's, whose answer
    says why it was replaced."""
    looks = handover.watching(home)
    app.state.handover = looks
    found = [runner.turn(home), watcher.turn(), handover.turn(looks)]
    inbox = getattr(app.state, "inbox_turn", None)
    if inbox is not None:
        found.append(inbox)
    return found


def recorded(home: Path, facts: server_facts.Facts) -> None:
    """Write the facts of the server that starts, and record its release, before it serves."""
    serve_file.write(home, facts)
    update.at_start(home, facts.install.version)


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
