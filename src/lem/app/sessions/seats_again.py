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
    from lem.records.holds import Hold
    from lem.records.record import Record
    from lem.records.work import StandIn


def again(here: Here, slug: str, now: datetime) -> Record:
    """Try again each seat whose agent failed with no fallback: clear its block, and end its
    stand-ins. A hold of the owner's that was there before stays."""
    record = tasks.read(here.where.state, slug)
    seats = waiting_seats(record)
    if not seats:
        raise Refusal(
            "no-seat-block",
            f"{slug} waits for no seat whose agent gave an error",
            f"lem task show {slug} says what it waits for",
        )
    change = partial(with_again, seats=seats, now=now)
    return tasks.update(here.where.state, slug, change, record.revision)


def waiting_seats(record: Record) -> frozenset[str]:
    """The seats whose agent failed with no fallback, and no go on since."""
    failures = (one for one in record.task.stand_ins if one.again is None)
    return frozenset(one.seat for one in failures if one.took is None)


def with_again(record: Record, *, seats: frozenset[str], now: datetime) -> Record:
    """The record with no block of those seats, each of their stand-ins ended, and the line
    of the go on."""
    task = record.task
    end = partial(ending, seats=seats, now=now)
    entry = StateNoted(at=now, status=task.status, line=go_on(seats))
    ended = tuple(map(end, task.stand_ins))
    changed = replace(task, hold=kept_hold(task.hold, seats), stand_ins=ended)
    return replace(record, task=changed, journal=(*record.journal, entry))


def go_on(seats: frozenset[str]) -> str:
    """The line of the owner's go on, with the seats it tries again."""
    named = ", ".join(sorted(seats))
    return f"the owner's go on: {named} tried again"


def kept_hold(hold: Hold | None, seats: frozenset[str]) -> Hold | None:
    """The hold after the go on: none for the block of those seats, any other as it was."""
    return None if isinstance(hold, Blocked) and hold.seat in seats else hold


def ending(stand_in: StandIn, *, seats: frozenset[str], now: datetime) -> StandIn:
    """A stand-in of those seats that still holds, ended at `now`; any other as it is."""
    holds = stand_in.seat in seats and stand_in.again is None
    return replace(stand_in, again=now) if holds else stand_in
