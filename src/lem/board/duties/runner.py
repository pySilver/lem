"""The board server's duties across tasks: every TICK seconds, each duty of DUTIES for each
workspace on the list, one at a time, never on a request's path.

Each duty is a module of this folder with `tick(workspace, now)`, found by its fixed path, so
that the step that builds one fills its module and edits neither this table nor the app. What a
failed duty costs the others (the seams of `serve.forge_loop`) is the step `board-duties`'s.
"""

import importlib
from typing import TYPE_CHECKING

import anyio

from lem.board import machine, workspaces
from lem.kernel import clock

if TYPE_CHECKING:
    from pathlib import Path

# How often the duties run, in seconds (`serve.FORGE_TICK` on `main`).
TICK = 20
DUTIES = (
    "lem.board.duties.forge",
    "lem.board.duties.merge",
    "lem.board.duties.conflict",
    "lem.board.duties.queue",
    "lem.board.duties.guard",
    "lem.board.duties.prune",
    "lem.board.duties.notify",
)


def tick(home: Path) -> None:
    """Run each duty once for each workspace of the list of Lem's home folder `home`."""
    host = machine.machine_name()
    now = clock.now()
    for name, _ in workspaces.named(workspaces.listed(home), host):
        space = workspaces.found(home, host, name)
        if space is None:
            continue
        for path in DUTIES:
            importlib.import_module(path).tick(space, now)


async def loop(home: Path, stopping: anyio.Event) -> None:
    """Run the duties every TICK seconds, off the event loop, until the server stops."""
    while not stopping.is_set():
        with anyio.move_on_after(TICK):
            await stopping.wait()
        if not stopping.is_set():
            await anyio.to_thread.run_sync(tick, home)
