"""`lem task worktree`: the task's worktree under `.lem/worktrees/`, on its branch, cut from
origin's base after a fetch (or from the branch a resume goes on from), with `checks.setup` run
once in it; or its path alone.

A worktree that is there already is taken as it is, so a run cut off after git made it makes no
second one. A branch that is the base or a protected one is refused, and so is a new branch that
origin has already and no task here holds: somebody's work, or a task of another machine.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks import heads, ports, release, where
from lem.app.tasks.setup import Ran, set_up
from lem.records.base import Frozen
from lem.settings.load import base_of, team_of
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.wiring import Ports
    from lem.records.record import Record

type Asked = tuple[str | None, Path | None]


class Made(Frozen, frozen=True, kw_only=True):
    """The worktree: its path, its branch, whether this call made it, and the setup it ran."""

    worktree: str
    branch: str | None = None
    made: bool = False
    said: str | None = None
    setup: tuple[Ran, ...] = ()


def branched(record: Record, *, branch: str) -> Record:
    """The record with the task's branch."""
    return replace(record, task=replace(record.task, branch=branch))


def made(
    given: Ports,
    workspace: places.Workspace,
    record: Record,
    asked: tuple[str | None, str | None],
) -> Made:
    """Make the worktree when it is not there, on the branch asked for (else the record's,
    else TYPE/SLUG), cut from the start asked for (else origin's base); put its branch on the
    record."""
    team = team_of(workspace.checkout)
    chosen = where.named(record, asked[0], team.branch)
    path = where.worktree(workspace, record.task.slug)
    fresh = not path.exists()
    said = None
    if fresh:
        said = heads.cut(
            given, workspace.checkout, path, (chosen, start_of(asked[1], base_of(team)))
        )
    else:
        heads.on_branch(path, chosen)
    tasks.update(
        workspace.state,
        record.task.slug,
        partial(branched, branch=chosen),
        record.revision,
    )
    return Made(
        worktree=str(path),
        branch=chosen,
        made=fresh,
        said=said,
        setup=prepared(workspace, record, path, team.checks.setup if fresh else ()),
    )


def start_of(start: str | None, base: str) -> str:
    """Where a new branch is cut from: the start asked for, else origin's base."""
    return start or f"origin/{base}"


def prepared(
    workspace: places.Workspace, record: Record, path: Path, commands: tuple[str, ...]
) -> tuple[Ran, ...]:
    """Run `checks.setup` in the worktree just made, with its log in the task's folder."""
    if not commands:
        return ()
    folder = places.task_folder(workspace.state, record.task.slug)
    return set_up(commands, path, folder)


def worktree(folder: Path, slug: str, *, path_only: bool, asked: Asked) -> Made:
    """`lem task worktree SLUG`: its path with `path_only`, else the worktree made."""
    workspace = places.workspace(folder)
    where.checkout_refusal(workspace, asked[1])
    record = release.checked(workspace.state, slug)
    if path_only:
        team_of(workspace.checkout)
        path = where.worktree(workspace, slug)
        return Made(worktree=str(path), branch=record.task.branch)
    return made(ports.bound(workspace), workspace, record, (asked[0], None))
