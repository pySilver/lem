"""What the review step reads from git besides the world: the change's size, its edits of Lem's
own settings files (`app/landing/review_edits.py`), the backlog folder at the base, and the
items the branch adds that `file` did not write (`land.due`, `land.careful`, `land.base_items`
and `land.branch_items` on `main`)."""

import shlex
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import backlog, bar_range, review_edits
from lem.model.landing import careful, review_due
from lem.records.base import Frozen
from lem.records.landing.checks import Edited
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.model.landing.items import BacklogItem


class Seen(Frozen, frozen=True, kw_only=True):
    """An item of the backlog as a reviewer is told of it: its path, `where` and title."""

    path: str
    where: str | None = None
    title: str


type Told = tuple[Seen, ...]


class Gathered(Frozen, frozen=True, kw_only=True):
    """The change's facts: its lines, the edits of the settings files, the base's backlog
    files and items, and the items the branch adds that no review's filing wrote."""

    lines: int
    edits: careful.Edits
    at_base: frozenset[str]
    backlog: Told = ()
    filed: Told = ()
    edited: tuple[Edited, ...] = ()


def told(found: Iterable[BacklogItem]) -> Told:
    """Items as a reviewer is told of them."""
    return msgspec.convert(tuple(found), Told, from_attributes=True)


def filed_by_others(context: Context, there: frozenset[str]) -> Told:
    """The items the branch adds that no review's filing wrote: the builder's and the
    polish pass's."""
    written = {filed.path for filed in (context.record.landing or Landing()).filed}
    tip = context.world.tip or ""
    found = backlog.added(context.ports.git, context.worktree, tip, there)
    return told(one for one in found if one.path not in written)


def gathered(context: Context) -> Gathered:
    """The facts of the change from origin's base to the worktree's tip: one diff, and one
    look at the base's backlog files."""
    git, worktree = context.ports.git, context.worktree
    span = (context.world.base, context.world.tip or "")
    stat = git.diff_stat(worktree, *span)
    there = backlog.files_at_base(git, worktree, span[0], stat.paths)
    return Gathered(
        lines=stat.added + stat.removed,
        edits=review_edits.edits(git, worktree, span, stat.paths),
        at_base=there,
        backlog=told(backlog.at_base(git, worktree, span[0], there)),
        filed=filed_by_others(context, there),
        edited=bar_range.for_review(context, span, stat.paths),
    )


def facts(context: Context, found: Gathered) -> review_due.Facts:
    """What `read --record` checks a review against."""
    checked = (context.record.landing or Landing()).checked
    paths = {one.path for one in checked.lowered} if checked else set()
    return review_due.Facts(
        careful=careful.reasons(context.record, found.edits, context.world.feature),
        folder=backlog.FOLDER,
        at_base=found.at_base,
        lowered=tuple(sorted(paths)),
    )


def rules_of(worktree: Path, span: str) -> str:
    """The command that gives the rules of the change's range, its path quoted for the
    shell."""
    return shlex.join(("lem", "--repo", str(worktree), "rules", "--range", span))
