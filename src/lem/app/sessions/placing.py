"""Where a task's session goes, and whether it may open now: the terminal's sessions, the
workspace of the task's newest session, and the task a queued task waits for.

A new session opens in the workspace of the task's newest session while that workspace is still
there, else in that of the task it is queued after, else in the caller's, which the terminal
knows. A queued task waits for the task its `after` names until that one landed or was
answered: a dropped one leaves it queued for the owner's word.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import opened
from lem.kernel.errors import Refusal
from lem.ports.terminal import Opening, Pane, Unreadable
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.task import Task

# The statuses that end a queued task's wait.
DONE = ("landed", "answered")


def listed(here: Here) -> dict[str, Pane]:
    """The terminal's sessions by id; refused when the terminal cannot say."""
    panes = here.ports.terminal.sessions()
    if isinstance(panes, Unreadable):
        raise Refusal(
            "terminal",
            f"agterm's sessions could not be read: {panes.why}",
            "the owner checks that agterm runs (lem doctor), then runs this again",
        )
    return {pane.id: pane for pane in panes}


def workspace_for(here: Here, task: Task) -> str | None:
    """The workspace of the task's newest session, else of the task it is queued after, while
    agterm still has it; None for the caller's."""
    known = {pane.workspace for pane in listed(here).values()}
    slugs = (task.slug, task.after) if task.after else (task.slug,)
    folders = (here.folder(slug) for slug in slugs)
    newest = (opened.newest_open(opened.read(folder)) for folder in folders)
    found = (line.workspace for line in newest if line is not None)
    return next((workspace for workspace in found if workspace in known), None)


def opening(here: Here, task: Task, line: str) -> Opening:
    """The task's session to open in the main checkout on the launch line `line`, in the
    workspace `workspace_for` gives."""
    workspace = workspace_for(here, task)
    cwd = str(here.where.checkout)
    return Opening(name=task.slug, cwd=cwd, command=(line,), workspace=workspace)


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
    raise Refusal(
        "queued-after",
        f"{task.slug} is queued after {task.after}, which is {status}",
        f"it opens when {task.after} landed or was answered; the owner's word starts it now: "
        f'lem task start {task.slug} --words "..."',
    )
