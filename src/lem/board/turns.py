"""The loops of the board server's life: each one a step, off the event loop, every period
until the server stops. The duties, the watcher of the notifications, the look at the server's
own install, and the Inbox's when it is on are each one `Turn`.

A step's failure never ends the server: one fault of a tick of the duties ended the whole
server through its task group on 2026-11-27, after `brew upgrade` removed the files of the
release that served. While a loop's last step failed, every board shows the problem, and the
next step that runs clears it. The traceback goes to the server's log at most once in
`memory.TRACE_EVERY` for each loop, with the count of the failures since. The wait comes before
each step, so a step that fails at once cannot spin.
"""

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import anyio

from lem.board.duties.memory import MEMORY, Traces
from lem.board.duties.seams import said_of

if TYPE_CHECKING:
    from collections.abc import Callable

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class Turn:
    """One loop of the server's life: its name on the board and in the log, its period in
    seconds, and its step."""

    name: str
    every: float
    step: Callable[[], object]


def problem_of(turn: Turn, error: Exception) -> str:
    """What every board shows while the loop's last step failed."""
    return (
        f"{turn.name} of the board server failed, and runs again every {turn.every:g} s: "
        f"{said_of(error)}"
    )


async def kept_up(turn: Turn, stopping: anyio.Event) -> None:
    """Run the loop's step every period until the server stops; a failure is the boards'
    problem until a step runs, and its traceback is in the server's log."""
    traces = Traces()
    while not stopping.is_set():
        with anyio.move_on_after(turn.every):
            await stopping.wait()
        if stopping.is_set():
            return
        try:
            await anyio.to_thread.run_sync(turn.step)
        except Exception as error:
            MEMORY.looped(turn.name, problem_of(turn, error))
            since = traces.due(turn.name, time.monotonic())
            if since is not None:
                LOGGER.exception(
                    "lem serve: %s of the board server failed, and runs again "
                    "(%d more failures of it since its last traceback)",
                    turn.name,
                    since,
                )
        else:
            MEMORY.looped(turn.name, None)
