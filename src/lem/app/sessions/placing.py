"""Where a task's new session goes: the workspace of agterm it opens in, and the opening the
terminal makes.

A new session opens in the workspace of the task's newest session, else the caller's, else that
of the task it is queued after, else that of the repository's newest session, while agterm still
has that workspace; with none of them it is refused (`session.workspace_for` on `main`).
"""

from typing import TYPE_CHECKING

from lem.app.sessions import log, seen
from lem.kernel.errors import Refusal
from lem.ports.terminal import Opening
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.task import Task


def workspace_for(here: Here, task: Task) -> str:
    """The workspace a new session of the task opens in; refused when nothing names one."""
    panes = seen.listed(here)
    known = {pane.workspace for pane in panes.values()}
    caller = panes.get((here.caller or "").upper())
    found = (
        workspace_of(here, task.slug),
        caller.workspace if caller else None,
        workspace_of(here, task.after),
        repository_newest(here),
    )
    chosen = next((space for space in found if space and space in known), None)
    if chosen is None:
        raise Refusal(
            "no-workspace",
            f"no workspace of agterm is known for {task.slug}: no session of it or of this "
            "repository is on record, and this runs in no session of agterm",
            f"run lem session open {task.slug} from a session in the workspace it belongs in",
        )
    return chosen


def workspace_of(here: Here, slug: str | None) -> str | None:
    """The workspace of the task's newest session, when Lem opened one and named it."""
    if slug is None:
        return None
    newest = log.newest_open(log.read(here.folder(slug)))
    return newest.workspace if newest else None


def repository_newest(here: Here) -> str | None:
    """The workspace of the newest session Lem opened for any task of the repository."""
    slugs = (one.task.slug for one in tasks.every(here.where.state))
    newest = log.newest_in(map(here.folder, slugs))
    return newest.workspace if newest else None


def opening(here: Here, task: Task, line: str) -> Opening:
    """The task's session to open in the main checkout on the launch line `line`."""
    workspace = workspace_for(here, task)
    cwd = str(here.where.checkout)
    return Opening(name=task.slug, cwd=cwd, command=(line,), workspace=workspace)
