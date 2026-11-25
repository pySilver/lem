"""Whether a queued task may get its session now: a task queued after others waits until each
of them landed or was answered; a dropped one leaves it queued for the owner's word, which
starts it or drops it (`session.queued_behind` on `main`)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.task import behind as dependencies
from lem.records.holds import ReleaseHold
from lem.store import tasks

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


def release_stop(task: Task) -> None:
    """Refuse a task two releases back (`lem_release.check` on `main`): its sessions, their
    wakes and their changes of phase wait for the owner's drop or resume; only the cleanup
    after a merge passes, as the caller decides."""
    if isinstance(task.hold, ReleaseHold):
        slug = task.slug
        raise Refusal("release", task.hold.say, f"lem task show {slug} says the way on")
