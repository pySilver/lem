"""`lem task plan-file`: the name a task's plan takes in the plans folder, and the plan the task
has now, in its worktree (`project.cmd_plan_file` and `plans.found` on `main`).

`[paths]` of the team's file names the plans folder and the pattern of a plan's name. A stand-in
reads that one table until the step `settings` gives the team's settings a `[paths]` table
(`notes/task.md`), as `tracker.kind_of` reads `[tracker]`.
"""

from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import msgspec

from lem.app.tasks import release, where
from lem.kernel import clock, errors
from lem.model.task import plans as names
from lem.records.base import Frozen
from lem.settings import places as settings_places
from lem.settings.load import tables
from lem.store import tasks

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.store.places import Workspace


class Paths(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """`[paths]`: the plans folder, the pattern of a plan's name, and the rulings file."""

    plans: str = "docs/plans"
    plan_file: str = names.PLAN_FILE
    rulings: str | None = None


class PlanFile(Frozen, frozen=True, kw_only=True):
    """The plan's name on the day, its path in the repository, and the plan the task has now
    (None before its lead writes one)."""

    slug: str
    pattern: str
    name: str
    path: str
    found: str | None = None


def paths_of(checkout: Path) -> Paths:
    """`[paths]` of the team's file of `checkout`, or its defaults."""
    path = checkout / settings_places.TEAM
    found = tables(path).get("paths") if path.is_file() else None
    if found is None:
        return Paths()
    try:
        return msgspec.convert(found, Paths)
    except msgspec.ValidationError as error:
        raise errors.Refusal(
            "settings",
            f"{path}: [paths] {error}",
            "correct the line as docs/settings.md says, then run the command again",
        ) from error


def folder_of(workspace: Workspace, slug: str, paths: Paths) -> Path:
    """The plans folder the task's plan is in: its worktree's when it has one, else the main
    checkout's."""
    worktree = workspace.lem / where.WORKTREES / slug
    root = worktree if worktree.is_dir() else workspace.checkout
    return root / paths.plans


def found(
    workspace: Workspace, record: Record, every: tuple[Record, ...]
) -> str | None:
    """The task's plan as a path in the repository, the newest day's; a resumed task's is the
    plan of the nearest task it came from until it has one of its own."""
    paths = paths_of(workspace.checkout)
    slug = record.task.slug
    folder = folder_of(workspace, slug, paths)
    files = (
        [path.name for path in folder.iterdir() if path.is_file()]
        if folder.is_dir()
        else []
    )
    named = names.newest(files, paths.plan_file, names.chain(slug, every))
    return str(PurePosixPath(paths.plans) / named) if named else None


def plan_file(workspace: Workspace, slug: str, day: str | None) -> PlanFile:
    """`lem task plan-file SLUG [--date DAY]`: the plan's name, written on `day` or today."""
    record = release.checked(workspace.state, slug)
    paths = paths_of(workspace.checkout)
    written = names.day_of(day, clock.now().date())
    name = names.name(paths.plan_file, slug, written)
    return PlanFile(
        slug=slug,
        pattern=paths.plan_file,
        name=name,
        path=str(PurePosixPath(paths.plans) / name),
        found=found(workspace, record, tasks.every(workspace.state)),
    )
