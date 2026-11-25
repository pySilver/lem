"""`lem task park` and the resume of a parked task: the owner's word to put a task aside, and
to bring it back as it was (`stages/park.md`).

The park and the hold it puts aside are one write, with the owner's answer when he parks from
the board. On resume a breaker gets a new question.
"""

from functools import partial
from typing import TYPE_CHECKING

import msgspec

from lem.app.decisions import writing
from lem.app.tasks import release
from lem.kernel import clock
from lem.model.task import holds
from lem.records import base
from lem.records import holds as hold_types
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


class Resumed(base.Frozen, frozen=True, kw_only=True):
    """What a resume did: the task it brought back or opened, how, from which task, its
    status, the breaker that waits again, and what the owner reads."""

    task: str
    resumed: str
    status: str | None = None
    origin: str | None = msgspec.field(default=None, name="from")
    branch: str | None = None
    breaker: int | None = None
    missing: str | None = None
    says: str


def parking(
    record: Record, *, why: str, now: base.Moment, answer: tasks.Change | None
) -> Record:
    """Park this revision with its answer, if the board has one for it."""
    if answer is not None:
        record = answer(record)
    return holds.parked(record, words=why, now=now)


def parked(
    folder: Path, slug: str, why: str, *, answer: tasks.Change | None = None
) -> Resumed:
    """Park the task `slug` on the owner's word `why`."""
    where = places.workspace(folder)
    release.checked(where.state, slug)
    change = partial(parking, why=why, now=clock.now(), answer=answer)
    record = writing.updated(where.state, slug, change)
    return Resumed(
        task=slug,
        resumed="parked",
        status=record.task.status,
        says=f"{slug} is put aside: its worktree, branch and files stay, and nothing of it "
        "waits for the owner",
    )


def brought_back(where: places.Workspace, record: Record) -> Resumed:
    """Bring a parked task back with the hold its park put aside."""
    slug = record.task.slug
    hold = record.task.hold
    before = hold.held if isinstance(hold, hold_types.Parked) else None
    change = partial(holds.resumed, before=before, now=clock.now())
    tasks.update(where.state, slug, change, record.revision)
    breaker = before.number if isinstance(before, hold_types.BreakerHold) else None
    return Resumed(
        task=slug,
        resumed="parked",
        status=record.task.status,
        breaker=breaker,
        says=f"{slug} goes on in its own worktree from where it was put aside",
    )
