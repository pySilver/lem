"""`lem task park` and the resume of a parked task: the owner's word to put a task aside, and
to bring it back as it was (`stages/park.md`).

The park keeps the hold it puts aside in `parked.json` of the task's folder, written before the
record, so that the resume gives it back: a breaker that waited waits again. A stand-in until the
record's `Parked` holds it itself (`notes/task.md`).
"""

from functools import partial
from typing import TYPE_CHECKING

import msgspec

from lem.app.tasks import release
from lem.kernel import clock, files
from lem.model.task import holds
from lem.records.base import Frozen
from lem.records.holds import BreakerHold, Hold, Parked
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

ASIDE = "parked.json"


class Aside(Frozen, frozen=True, kw_only=True):
    """The hold a park put aside."""

    hold: Hold | None = None


class Resumed(Frozen, frozen=True, kw_only=True):
    """What a resume did: the task it brought back or opened, how, from which task, its
    status, the breaker that waits again, and what the owner reads."""

    task: str
    resumed: str
    status: str | None = None
    origin: str | None = msgspec.field(default=None, name="from")
    branch: str | None = None
    breaker: int | None = None
    says: str


def parked(folder: Path, slug: str, why: str) -> Resumed:
    """Park the task `slug` on the owner's word `why`."""
    where = places.workspace(folder)
    record = release.checked(where.state, slug)
    refused = holds.park_refusal(record.task)
    if refused is not None:
        raise refused
    if not isinstance(record.task.hold, Parked):
        aside = msgspec.json.encode(Aside(hold=record.task.hold))
        files.write_whole(places.task_folder(where.state, slug) / ASIDE, aside)
    change = partial(holds.parked, words=why, now=clock.now())
    tasks.update(where.state, slug, change, record.revision)
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
    path = places.task_folder(where.state, slug) / ASIDE
    aside = (
        msgspec.json.decode(path.read_bytes(), type=Aside)
        if path.is_file()
        else Aside()
    )
    change = partial(holds.resumed, before=aside.hold, now=clock.now())
    tasks.update(where.state, slug, change, record.revision)
    path.unlink(missing_ok=True)
    breaker = aside.hold.number if isinstance(aside.hold, BreakerHold) else None
    return Resumed(
        task=slug,
        resumed="parked",
        status=record.task.status,
        breaker=breaker,
        says=f"{slug} goes on in its own worktree from where it was put aside",
    )
