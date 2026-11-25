"""A duty of the board server: the wake of a task whose landing ended, so that its session
cleans up (`wake … merged` of `serve.duties` on `main`).

A task the merge ended (`landed`, or `dropped` because its pull request was closed on the
forge) whose worktree is still there gets one wake, when no session of it was woken or opened
since it ended; with no live session the wake opens one.
"""

from typing import TYPE_CHECKING

from lem.app.landing.merged import CLOSED
from lem.board.duties import wakes
from lem.records.journal.task import StateNoted
from lem.store import tasks

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.records.record import Record


def tick(duty: Duty) -> None:
    """Wake each task whose landing ended and whose worktree stays."""
    for record in tasks.every(duty.state):
        slug = record.task.slug
        if not ended(record) or duty.here.worktree(slug) is None:
            continue
        if not wakes.since(duty, slug, record.task.since):
            wakes.woken(duty, slug, "merged")


def ended(record: Record) -> bool:
    """Whether the merge ended the task: it landed, or the forge closed its pull request."""
    status = record.task.status
    if status == "landed":
        return True
    states = [entry for entry in record.journal if isinstance(entry, StateNoted)]
    last = states[-1].line if states else None
    return status == "dropped" and (last or "").startswith(CLOSED)
