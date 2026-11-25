"""The life of the board server: its facts in `serve.json` while it runs, and its duties
beside it."""

from contextlib import asynccontextmanager
from functools import partial
from typing import TYPE_CHECKING

import anyio

from lem.board import serve_file
from lem.board.duties import runner

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from starlette.applications import Starlette
    from starlette.types import StatelessLifespan

    from lem.board.facts import Facts


@asynccontextmanager
async def lived(app: Starlette, *, facts: Facts, home: Path) -> AsyncIterator[None]:
    """The server's life: its facts in `serve.json` and its duties while it runs."""
    serve_file.write(home, facts)
    stopping = anyio.Event()
    async with anyio.create_task_group() as group:
        group.start_soon(runner.loop, home, stopping)
        yield
        stopping.set()
    serve_file.remove(home, facts.pid)


def lifespan(facts: Facts, home: Path) -> StatelessLifespan[Starlette]:
    """The life of the server `facts` of Lem's home folder `home`."""
    return partial(lived, facts=facts, home=home)
