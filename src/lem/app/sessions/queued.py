"""Whether a queued task may get its session now: a task queued after others waits until each
of them landed or was answered; a dropped one leaves it queued for the owner's word, which
starts it or drops it (`session.queued_behind` on `main`). A feature, which a part names, gets
its session for a sync while it waits for its parts (`board/duties/sync.py`)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.task import behind as dependencies
from lem.model.task import sync
from lem.records.holds import ReleaseHold
from lem.store import survey, tasks

# The open of a feature for its sync, before the turn of its end.
SYNC = "sync"

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.record import Record
    from lem.records.task import Task


def record_of(here: Here, slug: str) -> Record | None:
    """The dependency's record, or None when it does not read."""
    try:
        return tasks.read(here.where.state, slug)
    except Refusal:
        return None


def behind(here: Here, task: Task) -> None:
    """Refuse a queued task one of whose `after` tasks has not landed or been answered, or is
    not on record, a dropped one first: only the owner's word starts it then
    (`session.queued_behind` on `main`)."""
    if task.status != "queued":
        return
    records = (record_of(here, slug) for slug in task.after)
    refused = dependencies.behind(
        task, tuple(record for record in records if record is not None)
    )
    if refused is not None:
        start = dependencies.word(task.slug)
        raise Refusal(
            "queued-after", refused.why, f"the owner's word starts it now: {start}"
        )


def syncs(here: Here, task: Task, why: str) -> bool:
    """Whether the open is a feature's sync, which waits for no turn: its why is `sync`, and
    a part names the task."""
    if why != SYNC:
        return False
    every = survey.records(here.where.state).readable
    return sync.named(task.slug, (one.task for one in every))


def release_stop(task: Task) -> None:
    """Refuse a task two releases back (`lem_release.check` on `main`): its sessions, their
    wakes and their changes of phase wait for the owner's drop or resume; only the cleanup
    after a merge passes, as the caller decides."""
    if isinstance(task.hold, ReleaseHold):
        slug = task.slug
        raise Refusal("release", task.hold.say, f"lem task show {slug} says the way on")
