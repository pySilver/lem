"""The board server's duties across tasks: every TICK seconds, for each workspace on the list,
each duty of DUTIES in its order, one at a time, never on a request's path (`serve.forge_loop`
on `main`): the look at the forge first, the keeping of the state folder last.

Each duty is a module of this folder with `tick(duty)`, found by its fixed path. One failure
costs no other: a workspace whose ports do not bind is its board's problem, and the next
workspace still runs; a failed look at the forge is its board's problem, and the duties, the
keeping and the next workspace still run; a failed duty is its board's problem, and the other
duties, the keeping and the next workspace still run; a failed keeping is one line in the
server's log. A failure that is no refusal is a fault of Lem: its traceback goes to the server's
log too, at most once an hour for each duty, and each tick tries the step again. A failure of
the tick itself ends no server (`board/turns.py`). A workspace of example tasks (its state
folder holds `demo`) owes nothing.
"""

import os
from functools import partial
from typing import TYPE_CHECKING

from lem.board import machine, workspaces
from lem.board.duties import context, seams
from lem.board.duties.memory import MEMORY
from lem.board.turns import Turn
from lem.kernel import clock

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime
    from pathlib import Path

    from lem.store.places import Workspace

# How often the duties run, in seconds (`serve.FORGE_TICK` on `main`): a guess, short beside
# the forge's three minutes.
TICK = 20
NAME = "the duties"
DUTIES = (
    "lem.board.duties.forge",
    "lem.board.duties.merge",
    "lem.board.duties.conflict",
    "lem.board.duties.queue",
    "lem.board.duties.guard",
    "lem.board.duties.prune",
)
# The look at the forge, whose failure the board words as its own, and the keeping, whose
# failure is a line in the server's log only.
LOOK = "forge"
LOOK_FAILURE = "forge-duty"
KEEP = "prune"
DEMO = "demo"
# The board's problem of a workspace whose ports do not bind, so that no duty of it runs.
BIND = "duties"


def tick(home: Path, now: datetime | None = None) -> None:
    """Run the duties once for each workspace of the list of Lem's home folder `home`, with
    the server's environment."""
    moment = now or clock.now()
    for name, space in spaces(home):
        kept = MEMORY.of(space.checkout)
        here = seams.attempt(partial(context.bound, space, os.environ, home))
        if isinstance(here, seams.Failure):
            seams.noted(
                kept, name, BIND, f"the board's duties do not run: {here.said}", here
            )
            continue
        seams.noted(kept, name, BIND, None, None)
        ticked(context.Duty(name=name, here=here, now=moment, kept=kept))


def spaces(home: Path, host: str | None = None) -> Iterator[tuple[str, Workspace]]:
    """Each workspace of the list by its name, while Lem is set up in it, but one of example
    tasks."""
    host = host or machine.machine_name()
    for name, _ in workspaces.named(workspaces.listed(home), host):
        space = workspaces.found(home, host, name)
        if space is not None and not (space.state / DEMO).exists():
            yield name, space


def ticked(duty: context.Duty) -> None:
    """One workspace's tick: each duty, each failure kept apart."""
    for path in DUTIES:
        failed = seams.failure(path, duty)
        short = path.rsplit(".", 1)[-1]
        if short != KEEP:
            name = LOOK_FAILURE if short == LOOK else short
            seams.noted(duty.kept, duty.name, name, worded(short, failed), failed)
            continue
        seams.traced(duty.kept, duty.name, short, failed)
        if failed is not None:
            duty.say(f"lem prune failed: {failed.said}")


def worded(short: str, failed: seams.Failure | None) -> str | None:
    """The board's problem of a duty that failed, or None."""
    if failed is None:
        return None
    if short == LOOK:
        return f"the board's look at GitHub failed: {failed.said}"
    return f"the board's duty {short} failed: {failed.said}"


def turn(home: Path) -> Turn:
    """The duties as a loop of the server's life: a tick every TICK seconds."""
    return Turn(name=NAME, every=TICK, step=partial(tick, home))
