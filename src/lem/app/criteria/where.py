"""Where a task's criteria are: the workspace of the call, the task's folder, its `criteria.md`,
its worktree, and its plan in the worktree.

The plan is `docs/plans/YYYY-MM-DD-SLUG.md` in the task's worktree, the newest day's when there are
several, or, for a task resumed from a dropped one, the plan of the nearest task it came from that
has one, which its branch holds until its lead writes one of its own (`plans.found` on `main`).
The folder and the name are the settings' `paths.plans` and `paths.plan_file` once the step
`settings` reads them; until then these are their defaults.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.app.tasks import where
from lem.kernel import locks
from lem.kernel.errors import Refusal
from lem.store import places, tasks

if TYPE_CHECKING:
    from contextlib import AbstractContextManager
    from io import TextIOWrapper
    from pathlib import Path

    from lem.records.record import Record

NAME = "criteria.md"
LOCK = "criteria.lock"
PLANS = "docs/plans"
DAY = r"\d{4}-\d{2}-\d{2}"


@dataclass(frozen=True, kw_only=True, slots=True)
class Here:
    """A task's places: the workspace, the task's folder, and its worktree."""

    workspace: places.Workspace
    slug: str

    @property
    def folder(self) -> Path:
        """The task's folder in the state."""
        return places.task_folder(self.workspace.state, self.slug)

    @property
    def sheet(self) -> Path:
        """`criteria.md` in the task's folder: the interview's criteria, or the fast track's
        one criterion."""
        return self.folder / NAME

    @property
    def worktree(self) -> Path:
        """The task's worktree, which nothing here makes."""
        return self.workspace.lem / where.WORKTREES / self.slug

    def held(self) -> AbstractContextManager[TextIOWrapper]:
        """The task's criteria lock, which a change of its criteria and an approval of them
        hold over their write of the record and of `criteria.md` (`criteria.lock` on
        `main`): of two at one time, one ends before the other reads."""
        return locks.held(self.folder / LOCK)

    def read(self) -> Record:
        """The task's record."""
        return tasks.read(self.workspace.state, self.slug)


def here_of(folder: Path, slug: str) -> Here:
    """The places of the task `slug` of the workspace `folder` is in."""
    workspace = places.workspace(folder)
    places.task_folder(workspace.state, slug)
    return Here(workspace=workspace, slug=slug)


def own_plan(folder: Path, slug: str) -> Path | None:
    """The plan of `slug` in the plans folder, the newest day's; None when it has none."""
    form = re.compile(rf"({DAY})-{re.escape(slug)}\.md")
    if not folder.is_dir():
        return None
    names = (path.name for path in folder.iterdir())
    named = sorted(name for name in names if form.fullmatch(name))
    return folder / named[-1] if named else None


def plan_of(here: Here, record: Record) -> Path | None:
    """The task's plan in its worktree, or the plan of the nearest task it came from that has
    one; None when there is none."""
    folder = here.worktree / PLANS
    chain = [record.task.slug]
    came = record.task.resumed_from
    while came is not None and came not in chain:
        chain.append(came)
        came = tasks.read(here.workspace.state, came).task.resumed_from
    found = (own_plan(folder, slug) for slug in chain)
    return next((plan for plan in found if plan is not None), None)


def worktree_of(here: Here) -> Path:
    """The task's worktree; refused before it has one."""
    worktree = here.worktree
    if not (worktree / ".git").exists():
        raise Refusal(
            "no-worktree",
            f"{here.slug} has no worktree at {worktree}",
            f"lem task worktree {here.slug} makes it",
        )
    return worktree
