"""`lem task open`: a task's record and its folder, under the workspace's claim lock.

The task opens `shaping`, or `queued` behind the tasks `--after` names, with the owner's words as
he gave them. A ticket, a backlog item and the dropped task it goes on from are claimed under the
lock with the scan of every record (`model/task/claim.py`); a part joins its feature's `after`
there too (`feature.py`). The same words again under the same slug are a retry and pass; other
words are another request under the same name (`open_again.py`).
"""

from typing import TYPE_CHECKING

from lem.app.tasks import feature, open_again, taken
from lem.app.tasks.opening import fresh
from lem.kernel import clock, locks
from lem.model.task import claim, part_of
from lem.records.base import Frozen
from lem.settings.load import settings_of
from lem.store import places, tasks, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.tasks.opening import Asked
    from lem.records.task import Task
    from lem.records.tickets import Tracker


class Opened(Frozen, frozen=True, kw_only=True):
    """The task opened: its slug, its folder and its status, and whether this call made it."""

    slug: str
    folder: str
    status: str
    made: bool = True
    said: str | None = None


def opened(folder: Path, asked: Asked) -> Opened:
    """Open the task `asked` names, from the folder of the call: a branch origin has is
    refused before its record is written."""
    found = places.workspace(folder)
    state = places.state_of(found.checkout)
    tracker = settings_of(found.checkout).settings.tracker
    kind = tracker.kind if tracker else None
    if asked.part_of is not None and asked.ticket is not None:
        raise part_of.ticketed(asked.slug)
    with locks.held(places.locks_folder(state) / workspace.LOCK):
        retry = open_again.existing(found, tasks.every(state), asked, kind)
        if retry is not None:
            return made_by(state, retry, made=False)
    return published(found, asked, kind)


def published(found: places.Workspace, asked: Asked, kind: Tracker | None) -> Opened:
    """Check origin for the new task's branch, then claim and write its record."""
    said = taken.checked(found, asked.slug, asked.branch)
    with locks.held(places.locks_folder(found.state) / workspace.LOCK):
        return created(found, asked, kind, said)


def created(
    found: places.Workspace, asked: Asked, kind: Tracker | None, said: str | None
) -> Opened:
    """Under the claim lock, return a prior start or check the item and publish."""
    every = tasks.every(found.state)
    retry = open_again.existing(found, every, asked, kind)
    if retry is not None:
        return made_by(found.state, retry, made=False)
    joining = feature.joinable(found, every, asked)
    record = fresh(found, asked, kind, clock.now())
    written = workspace.published(found.state, claim.claimed(record, every, kind))
    if joining is not None:
        feature.added(found, joining, asked.slug)
    return made_by(found.state, written.task, said=said)


def made_by(
    state: Path, task: Task, *, made: bool = True, said: str | None = None
) -> Opened:
    """What the open prints of the task's record."""
    slug = task.slug
    where = str(places.task_folder(state, slug))
    return Opened(slug=slug, folder=where, status=task.status, made=made, said=said)
