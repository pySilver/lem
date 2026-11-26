"""Small worlds for the rules of the views: a few tasks made from records a case names, each
with its session, at a fixed minute, for the owner on this Mac."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.board.inputs.layout import Viewer
from lem.board.views.world import Clock, Place, Seen, World
from lem.model.owner.looks import Session
from lem.records.journal.task import StateNoted

NOW = MOMENT + timedelta(hours=1)
UTC = ZoneInfo("UTC")
VIEWER = Viewer(
    host="studio", workspace="shop", base="/studio/shop", local=True, may_act=True
)
PLACE = Place(repo="shop", base="main", path="/work/shop")


def live(minutes: float = 0, *, working: bool = False) -> Session:
    """A session that lives, opened `minutes` after the record's moment."""
    return Session(
        live=True, since=MOMENT + timedelta(minutes=minutes), working=working
    )


def gone() -> Session:
    """A session that does not live."""
    return Session(live=False, since=MOMENT)


def task(slug: str = "gift-note", line: str | None = None, **fields: object) -> Seen:
    """A task `slug` with the record's `fields`, its newest state `line`, and a live
    session."""
    made = record(slug, **fields)
    if line is not None:
        noted = StateNoted(at=made.task.since, status=made.task.status, line=line)
        made = replace(made, journal=(*made.journal, noted))
    cards = frozenset(one.id for one in made.task.questions if one.topic == "card")
    return Seen(record=made, session=replace(live(), cards=cards))


def world(*tasks: Seen, now: datetime = NOW) -> World:
    """The world of `tasks` at `now`."""
    clock = Clock(now=now, zone=UTC)
    return World(viewer=VIEWER, clock=clock, version="v", place=PLACE, tasks=tasks)
