"""Small worlds for the views of time: a task's record at a clock time of one day, Lem's acts on
its sessions beside it, and the world of a few such tasks at a minute of that day, for the owner
on this Mac.

The day is 2026-11-22, the day of `main`'s cases of the guard (merge-leaves-board-lock, #37).
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import msgspec

from fakes.records import record
from lem.board.inputs.layout import Viewer
from lem.board.views.world import Clock, Place, Seen, World

if TYPE_CHECKING:
    from lem.app.sessions.acts import Act
    from lem.records.journal.entry import Entry
    from lem.records.record import Record

SLUG = "gift-note"
BASE = "/h/w"
VIEWER = Viewer(host="h", workspace="w", base=BASE, local=True, may_act=True)
PLACE = Place(repo="shop", base="main", path="/work/shop")


def at(clock: str) -> datetime:
    """The moment `11:49` or `11:49:30` of the day, in UTC."""
    hours, minutes, *seconds = (int(part) for part in clock.split(":"))
    return datetime(2026, 11, 22, hours, minutes, *seconds, tzinfo=UTC)


def task(*journal: Entry, **fields: object) -> Record:
    """The task `gift-note` with its journal and the task's fields `fields`."""
    made = record(SLUG, **fields)
    return msgspec.structs.replace(made, journal=journal)


def named(slug: str, made: Record) -> Record:
    """The record `made` of the task `slug`."""
    renamed = msgspec.structs.replace(made.task, slug=slug)
    return msgspec.structs.replace(made, task=renamed)


def seen(made: Record, *acts: Act) -> Seen:
    """A task's record with Lem's acts on its sessions."""
    return Seen(record=made, acts=acts)


def world(*tasks: Seen, now: str = "13:00", viewer: Viewer = VIEWER) -> World:
    """The world of `tasks` at the clock time `now`, in UTC."""
    return World(
        viewer=viewer,
        clock=Clock(now=at(now), zone=UTC),
        version="1",
        place=PLACE,
        tasks=tasks,
    )
