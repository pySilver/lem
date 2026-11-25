"""`start`: the landing of a ready task begins (`landing.md` B and C, row 1).

It holds while the round has started, the worktree is clean and the settings name a command of
the checks. A new round from `open`, a conflict on the forge and the hold of "no checks" are the
step `land-base`'s.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing.world import Due, Held, World, later
from lem.records.landing.start import Started

if TYPE_CHECKING:
    from lem.records.record import Record

STEP = "start"


def unready(world: World) -> Refusal | None:
    """Why the worktree may not land as it is: gone, with changes nobody committed, or with no
    command of the checks to run."""
    if world.tip is None:
        return Refusal(
            "no-worktree",
            f"the task has no worktree on {world.branch}",
            "lem task worktree SLUG makes it",
        )
    if not world.clean:
        return Refusal(
            "dirty",
            "the task's worktree has changes nobody committed",
            "the builder commits them or removes them, then lem land start runs again",
        )
    if not world.rules.commands:
        return Refusal(
            "no-checks",
            "the settings name no command of the checks, so nothing would run",
            "write the whole suite into checks.commands of .lem/settings.toml; the hold "
            "that waits for it is the step `land-base`'s",
        )
    return None


def holds(record: Record, world: World) -> Held | Due:
    """Whether this round's start stands for the world now."""
    landing = record.landing
    started = landing.started if landing else None
    if landing is None or started is None or started.round != landing.round:
        return Due(step=STEP, why="this round of the landing has not started")
    refused = unready(world)
    if refused is not None:
        return Due(step=STEP, why=refused.why)
    return Held(why=f"round {started.round} started")


def decide(record: Record, world: World, *, conflicting: bool) -> Refusal | Started:
    """The start of round 1 of a ready task, or of a task in `landing` that a stop cut
    (its record kept whole), or why it may not start."""
    slug, status = record.task.slug, record.task.status
    if conflicting:
        return later("lem land start --conflicting", "land-base")
    if status not in {"ready", "landing"}:
        return Refusal(
            "status",
            f"{slug} is {status}: a task lands once it is ready",
            f"lem task move {slug} ready, once its builder's change is committed",
        )
    return unready(world) or Started(
        round=1, branch=world.branch, base_ref=world.rules.base, at=world.now
    )
