"""The life of the board server: its facts in `serve.json` while it runs, and beside it its
loops: the duties, the watcher of the board's notifications, the Inbox's when it is on, and the
look at its own install (`handover.py`).

A loop's failure never ends the server (`seams.kept_up`): one fault of a tick of the duties
ended the whole server through its task group on 2026-11-27, after `brew upgrade` removed the
files of the release that served. Its traceback goes to the server's log, and the loop starts
again; each loop waits before its first step, so its next try is one period later.
"""

from contextlib import asynccontextmanager
from functools import partial
from typing import TYPE_CHECKING

import anyio

from lem.board import facts as server_facts
from lem.board import handover, serve_file, update
from lem.board.duties import runner, seams

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
        for name, each in loops_of(app, home, watcher):
            group.start_soon(seams.kept_up, name, each, stopping)
        try:
            yield
        finally:
            stopping.set()
            await stopped(app)
    serve_file.remove(home, facts.pid)


def loops_of(
    app: Starlette, home: Path, watcher: Watcher
) -> list[tuple[str, seams.Loop]]:
    """The loops of the server's life, each by its name in the server's log."""
    loops: list[tuple[str, seams.Loop]] = [
        ("the duties", partial(runner.loop, home)),
        ("the watcher of the notifications", watcher.loop),
        ("the look at its install", partial(handover.loop, handover.watching(home))),
    ]
    inbox = getattr(app.state, "inbox_duty", None)
    if inbox is not None:
        loops.append(("the look at the Inbox", inbox))
    return loops


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
