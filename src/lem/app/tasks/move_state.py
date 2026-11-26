"""The facts of a task's worktree at a move, kept with that move in the journal."""

import os
from typing import TYPE_CHECKING, NamedTuple

from msgspec.structs import replace

from lem.adapters.git_cli_shell import Shell
from lem.app.tasks import heads, where
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.store.places import Workspace
    from lem.store.tasks import Change


class Worktree(NamedTuple):
    """The branch and the commit in the task's worktree, if there is one."""

    branch: str | None = None
    head: str | None = None
    subject: str | None = None


def gathered(workspace: Workspace, slug: str) -> Worktree:
    """Read the task's worktree without making it or its parent folder."""
    path = workspace.lem / where.WORKTREES / slug
    if not (path / ".git").is_file():
        return Worktree()
    git = Shell(environ=os.environ)
    logged = git.said(path, "log", "-1", "--format=%H%x00%s")
    head, subject = logged.split("\0", 1)
    return Worktree(heads.branch_on(path), head, subject or None)


def opening_of(record: Record, status: str) -> str | None:
    """The direct start of the build keeps the current read's first line."""
    if record.task.status != "shaping" or status != "building":
        return None
    state = next(
        (entry for entry in reversed(record.journal) if isinstance(entry, StateNoted)),
        None,
    )
    return None if state is None else state.opening


def noted(record: Record, worktree: Worktree, opening: str | None = None) -> Record:
    """Bind the newest state to the Git facts and, for the direct start, its read."""
    entry = record.journal[-1]
    if not isinstance(entry, StateNoted):
        raise TypeError("a task move must end with a state entry")
    marked = replace(
        entry,
        opening=opening,
        branch=worktree.branch,
        head=worktree.head,
        subject=worktree.subject,
    )
    task = record.task
    if task.branch is None and worktree.branch is not None:
        task = replace(task, branch=worktree.branch)
    journal = (*record.journal[:-1], marked)
    return replace(record, task=task, journal=journal)


def changed(record: Record, *, move: Change, worktree: Worktree) -> Record:
    """Apply the move and attach what its worktree showed."""
    moved = move(record)
    return noted(moved, worktree, opening_of(record, moved.task.status))
