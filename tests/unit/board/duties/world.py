"""A workspace for a duty of the board server: a checkout with Lem set up on fakes (as a task's
session has it, `unit.sessions.world`), its tasks, the forge's last look, and the duty at one
moment with what the server keeps of the workspace."""

from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from fakes.records import record
from lem.app.owner import forge
from lem.board.duties.context import Duty
from lem.board.duties.memory import Kept
from lem.records.landing.record import Landing, Pull
from lem.store import tasks
from unit.owner.looked import TIP

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.records.record import Record

PULL = Pull(number=44, url="https://github.com/o/r/pull/44", title="Gift note")


def duty_of(here: Here, now: datetime, kept: Kept | None = None) -> Duty:
    """The duty of the workspace `here` at `now`."""
    return Duty(name="shop", here=here, now=now, kept=kept or Kept())


def opened(here: Here, slug: str, **landing: object) -> Record:
    """An open task with pull request 44 and the landing's `landing` fields, on record."""
    made = replace(Landing(phase="open", pull=PULL), **landing)
    found = replace(record(slug, status="open"), landing=made)
    return tasks.create(here.where.state, found)


def landing_of(found: Record) -> Landing:
    """The landing of a task on record, which an open task has."""
    assert found.landing is not None
    return found.landing


def looked(here: Here, slug: str, mergeable: str, head: str = TIP) -> None:
    """The forge's last look: the task's pull request at `head`, as GitHub calls it."""
    seen = {slug: forge.Seen(head=head, mergeable=mergeable)}
    look = forge.Look(seen=seen)
    (here.where.state / forge.LOOK).write_bytes(msgspec.json.encode(look))
