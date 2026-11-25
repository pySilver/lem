"""Whether a queued task may get its session now: a task queued after another waits until that
one landed or was answered; a dropped one leaves it queued for the owner's word, which starts
it or drops it (`session.queued_behind` on `main`)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.task import Task

# The statuses that end a queued task's wait.
DONE = ("landed", "answered")


def behind(here: Here, task: Task) -> None:
    """Refuse a queued task whose `after` task has not landed or been answered, or is not on
    record: only the owner's word starts it then (`session.queued_behind` on `main`)."""
    if task.status != "queued" or task.after is None:
        return
    try:
        status = tasks.read(here.where.state, task.after).task.status
    except Refusal:
        status = "not on record"
    if status in DONE:
        return
    waits = (
        "it waits for the owner's word, which starts it or drops it"
        if status == "dropped"
        else (f"it opens when {task.after} landed or was answered")
    )
    raise Refusal(
        "queued-after",
        f"{task.slug} is queued after {task.after}, which is {status}: {waits}",
        f'the owner\'s word starts it now: lem task start {task.slug} --words "..."',
    )
