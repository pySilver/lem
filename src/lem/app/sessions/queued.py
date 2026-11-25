"""Whether a queued task may get its session now: a task queued after others waits until each
of them landed or was answered; a dropped one leaves it queued for the owner's word, which
starts it or drops it (`session.queued_behind` on `main`)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.records.holds import ReleaseHold
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.task import Task

# The statuses that end a queued task's wait.
DONE = ("landed", "answered")


def status_of(here: Here, slug: str) -> str:
    """The status of the task `slug`, or `not on record`."""
    try:
        return tasks.read(here.where.state, slug).task.status
    except Refusal:
        return "not on record"


def behind(here: Here, task: Task) -> None:
    """Refuse a queued task one of whose `after` tasks has not landed or been answered, or is
    not on record, a dropped one first: only the owner's word starts it then
    (`session.queued_behind` on `main`)."""
    if task.status != "queued":
        return
    statuses = ((after, status_of(here, after)) for after in task.after)
    waits = sorted(
        ((after, status) for after, status in statuses if status not in DONE),
        key=lambda pair: pair[1] != "dropped",
    )
    if not waits:
        return
    after, status = waits[0]
    then = (
        "it waits for the owner's word, which starts it or drops it"
        if status == "dropped"
        else (f"it opens when {after} landed or was answered")
    )
    raise Refusal(
        "queued-after",
        f"{task.slug} is queued after {after}, which is {status}: {then}",
        f'the owner\'s word starts it now: lem task start {task.slug} --words "..."',
    )


def release_stop(task: Task) -> None:
    """Refuse a task two releases back (`lem_release.check` on `main`): its sessions, their
    wakes and their changes of phase wait for the owner's drop or resume; only the cleanup
    after a merge passes, as the caller decides."""
    if isinstance(task.hold, ReleaseHold):
        slug = task.slug
        raise Refusal("release", task.hold.say, f"lem task show {slug} says the way on")
