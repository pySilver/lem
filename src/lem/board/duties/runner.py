"""The board server's duties across tasks: every TICK seconds, for each workspace on the list,
each duty of DUTIES in its order, one at a time, never on a request's path (`serve.forge_loop`
on `main`): the look at the forge first, the keeping of the state folder last.

Each duty is a module of this folder with `tick(duty)`, found by its fixed path. One failure
costs no other: a failed look at the forge is its board's problem, and the duties, the keeping
and the next workspace still run; a failed duty is its board's problem, and the other duties,
the keeping and the next workspace still run; a failed keeping is one line in the server's log.
A workspace of example tasks (its state folder holds `demo`) owes nothing.
"""

import os
from typing import TYPE_CHECKING

import anyio

from lem.board import machine, workspaces
from lem.board.duties import context
from lem.board.duties.memory import MEMORY
from lem.board.duties.seams import failure
from lem.kernel import clock

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime
    from pathlib import Path

    from lem.store.places import Workspace

# How often the duties run, in seconds (`serve.FORGE_TICK` on `main`): a guess, short beside
# the forge's three minutes.
TICK = 20
DUTIES = (
    "lem.board.duties.forge",
    "lem.board.duties.merge",
    "lem.board.duties.conflict",
    "lem.board.duties.queue",
    "lem.board.duties.guard",
    "lem.board.duties.notify",
    "lem.board.duties.prune",
)
# The look at the forge, whose failure the board words as its own, and the keeping, whose
# failure is a line in the server's log only.
LOOK = "forge"
KEEP = "prune"
DEMO = "demo"


def tick(home: Path, now: datetime | None = None) -> None:
    """Run the duties once for each workspace of the list of Lem's home folder `home`, with
    the server's environment."""
    moment = now or clock.now()
    for name, space in spaces(home):
        here = context.bound(space, os.environ, home)
        kept = MEMORY.of(space.checkout)
        ticked(context.Duty(name=name, here=here, now=moment, kept=kept))


def spaces(home: Path) -> Iterator[tuple[str, Workspace]]:
    """Each workspace of the list by its name, while Lem is set up in it, but one of example
    tasks."""
    host = machine.machine_name()
    for name, _ in workspaces.named(workspaces.listed(home), host):
        space = workspaces.found(home, host, name)
        if space is not None and not (space.state / DEMO).exists():
            yield name, space


def ticked(duty: context.Duty) -> None:
    """One workspace's tick: each duty, each failure kept apart."""
    for path in DUTIES:
        failed = failure(path, duty)
        short = path.rsplit(".", 1)[-1]
        if short != KEEP:
            noted(duty, short, worded(short, failed))
        elif failed is not None:
            duty.say(f"lem prune failed: {failed}")


def worded(short: str, failed: str | None) -> str | None:
    """The board's problem of a duty that failed, or None."""
    if failed is None:
        return None
    if short == LOOK:
        return f"the board's look at GitHub failed: {failed}"
    return f"the board's duty {short} failed: {failed}"


def noted(duty: context.Duty, name: str, problem: str | None) -> None:
    """Show the problem on the workspace's board and in the server's log, or forget it."""
    if problem is None:
        duty.kept.problems.pop(name, None)
        return
    duty.kept.problems[name] = problem
    duty.say(problem)


async def loop(home: Path, stopping: anyio.Event) -> None:
    """Run the duties every TICK seconds, off the event loop, until the server stops."""
    while not stopping.is_set():
        with anyio.move_on_after(TICK):
            await stopping.wait()
        if not stopping.is_set():
            await anyio.to_thread.run_sync(tick, home)
