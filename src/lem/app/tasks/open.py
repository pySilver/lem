"""`lem task open`: a task's record and its folder, under the workspace's claim lock.

The task opens `shaping`, or `queued` behind the task `--after` names, with the owner's words as
he gave them. A ticket, a backlog item and the dropped task it goes on from are claimed under the
lock with the scan of every record (`model/task/claim.py`). The same words again under the same
slug are a retry and pass; other words are another request under the same name.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import taken, tracker
from lem.app.tasks.opening import Asked, fresh, ticket_of
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.task import claim
from lem.records.base import Frozen
from lem.store import places, tasks, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record
    from lem.records.tickets import Ticket, Tracker


class Opened(Frozen, frozen=True, kw_only=True):
    """The task opened: its slug, its folder and its status, and whether this call made it."""

    slug: str
    folder: str
    status: str
    made: bool = True
    said: str | None = None


def again(state: Path, asked: Asked, ticket: Ticket | None) -> Record | None:
    """The task of the same slug when its words and its ticket are the same (a retry), or
    None when there is none; refused when it holds other words, another ticket, or ended."""
    every = tasks.every(state)
    same = (one for one in every if one.task.slug == asked.slug)
    found = next(same, None)
    if found is None:
        return None
    task = found.task
    if task.status in claim.ENDED:
        raise Refusal(
            "task-ended",
            f"the task {task.slug} is {task.status}, and a new task takes a slug of its own",
            "add a word to the slug",
        )
    if task.ask.split() != asked.ask.split():
        raise Refusal(
            "task-exists",
            f"the task {task.slug} holds other words already ({task.ask!r}), and a "
            "task's words are written once",
            "this is another request under the same name: add a word to the slug",
        )
    if ticket is not None and not claim.same(task.ticket, ticket):
        raise Refusal(
            "task-exists",
            f"the task {task.slug} holds another ticket than {ticket.id}",
            f"give the task for {ticket.id} another slug",
        )
    return found


def opened(folder: Path, asked: Asked) -> Opened:
    """Open the task `asked` names, from the folder of the call: a branch origin has is
    refused before its record is written."""
    found = places.workspace(folder)
    state = places.state_of(found.checkout)
    kind = tracker.kind_of(found.checkout)
    retry = again(state, asked, ticket_of(asked, kind))
    if retry is not None:
        return made_by(state, retry, made=False)
    return published(found, asked, kind)


def published(found: places.Workspace, asked: Asked, kind: Tracker | None) -> Opened:
    """Check origin for the new task's branch, then claim and write its record."""
    record = fresh(found, asked, kind, clock.now())
    said = taken.checked(found, asked.slug, asked.branch)
    written = workspace.claimed(found.state, partial(claim.claimed, record, kind=kind))
    return made_by(found.state, written, said=said)


def made_by(
    state: Path, record: Record, *, made: bool = True, said: str | None = None
) -> Opened:
    """What the open prints of the task's record."""
    slug = record.task.slug
    where = str(places.task_folder(state, slug))
    return Opened(
        slug=slug, folder=where, status=record.task.status, made=made, said=said
    )
