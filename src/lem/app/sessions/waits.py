"""The loop of `lem session wait --until STATES | --event KIND`: one look at each turn, then a
pause, until one of the ends of `waiting` comes."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions import wait_ends, waiting
from lem.records.base import Frozen
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.records.holds import Hold

type Clock = Callable[[], datetime]


class Asked(Frozen, frozen=True, kw_only=True):
    """The wait asked for: the task, the statuses or the kind that end it, the companion and
    the quiet file that end it too, and the seconds between two looks."""

    slug: str
    until: tuple[str, ...] = ()
    event: str | None = None
    companion: str | None = None
    quiet: str | None = None
    every: float


def wait_for(
    here: Here, asked: Asked, clock: Clock, pause: Callable[[float], None]
) -> waiting.Waited:
    """Look until the wait ends; each look reads the files and the terminal again."""
    before = waiting.counted(here, asked.slug, asked.event)
    began = clock()
    ended = None
    while ended is None:
        ended = looked(here, asked, before, began, clock())
        if ended is None:
            pause(asked.every)
    return ended


def looked(
    here: Here, asked: Asked, before: int, began: datetime, now: datetime
) -> waiting.Waited | None:
    """One look: how the wait ends now, or None while it goes on."""
    task = tasks.read(here.where.state, asked.slug).task
    base = waiting.Waited(task=task.slug, status=task.status, since=task.since)
    entry = (
        waiting.entry_of(here, asked.slug, asked.event, before) if asked.event else None
    )
    held = hold_word(task.hold)
    if entry is not None or {task.status, held} & set(asked.until):
        return msgspec.structs.replace(base, entry=entry, hold=held)
    return wait_ends.otherwise(here, asked, base, (began, now))


def hold_word(hold: Hold | None) -> str | None:
    """The word `--until` names a hold by: `held` for the owner's or a breaker's, else
    `blocked`, `parked` or `release`, as `main`'s states named them."""
    if hold is None:
        return None
    if isinstance(hold, (OwnerHold, BreakerHold)):
        return "held"
    words = (("blocked", Blocked), ("parked", Parked))
    return next((word for word, kind in words if isinstance(hold, kind)), "release")
