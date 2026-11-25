"""`lem task worktree`: the task's worktree under `.lem/worktrees/`, on its branch, cut from
origin's base after a fetch, and the branch on the record; or its path alone.

A worktree that is there already is taken as it is, so a run cut off after git made it makes no
second one. A branch that is the base or a protected one is refused. `checks.setup`, another
main checkout and the check of the branch's name are the step `task`'s.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import frame
from lem.app.tasks import where
from lem.model.landing.world import later
from lem.records.base import Frozen
from lem.settings.load import base_of, team_of
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


class Made(Frozen, frozen=True, kw_only=True):
    """The worktree: its path, its branch, and whether this call made it."""

    worktree: str
    branch: str | None = None
    made: bool = False


def branched(record: Record, *, branch: str) -> Record:
    """The record with the task's branch."""
    return replace(record, task=replace(record.task, branch=branch))


def added(workspace: places.Workspace, path: Path, branch: str, base: str) -> None:
    """Fetch origin, and add the worktree on `branch` cut from origin's `base`."""
    git = frame.bound(workspace).git
    git.fetch(workspace.checkout)
    git.worktree_add(workspace.checkout, path, branch, f"origin/{base}")


def made(workspace: places.Workspace, record: Record, branch: str | None) -> Made:
    """Make the worktree when it is not there, and put its branch on the record."""
    team = team_of(workspace.checkout)
    if team.checks.setup:
        raise later("checks.setup in a new worktree", "task")
    chosen = where.named(record, branch, team.branch)
    path = where.worktree(workspace, record.task.slug)
    fresh = not path.exists()
    if fresh:
        added(workspace, path, chosen, base_of(team))
    tasks.update(
        workspace.state,
        record.task.slug,
        partial(branched, branch=chosen),
        record.revision,
    )
    return Made(worktree=str(path), branch=chosen, made=fresh)


def worktree(folder: Path, slug: str, *, path_only: bool, branch: str | None) -> Made:
    """`lem task worktree SLUG`: its path with `path_only`, else the worktree made."""
    workspace = places.workspace(folder)
    record = tasks.read(workspace.state, slug)
    if path_only:
        path = where.worktree(workspace, slug)
        return Made(worktree=str(path), branch=record.task.branch)
    return made(workspace, record, branch)
