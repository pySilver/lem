"""`lem seat again`: the owner's go on over a task that a seat's error blocked: the block goes,
each stand-in of that seat ends, and the seat the settings name opens again
(`project.cmd_seat_again` on `main`)."""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.records.holds import Blocked
from lem.records.journal.task import StateNoted
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.records.record import Record
    from lem.records.work import StandIn


def again(here: Here, slug: str, now: datetime) -> Record:
    """Clear the block of a seat's error, and end its stand-ins."""
    record = tasks.read(here.where.state, slug)
    hold = record.task.hold
    if not isinstance(hold, Blocked) or hold.seat is None:
        raise Refusal(
            "no-seat-block",
            f"{slug} waits for no seat whose agent gave an error",
            f"lem task show {slug} says what it waits for",
        )
    change = partial(with_again, seat=hold.seat, now=now)
    return tasks.update(here.where.state, slug, change, record.revision)


def with_again(record: Record, *, seat: str, now: datetime) -> Record:
    """The record with no block, each stand-in of `seat` ended, and the line of the go on."""
    task = record.task
    end = partial(ending, seat=seat, now=now)
    entry = StateNoted(at=now, status=task.status, line=f"the owner's go on: {seat}")
    ended = map(end, task.stand_ins)
    changed = replace(task, hold=None, stand_ins=tuple(ended))
    return replace(record, task=changed, journal=(*record.journal, entry))


def ending(stand_in: StandIn, *, seat: str, now: datetime) -> StandIn:
    """A stand-in of `seat` that still holds, ended at `now`; any other as it is."""
    holds = stand_in.seat == seat and stand_in.again is None
    return replace(stand_in, again=now) if holds else stand_in
