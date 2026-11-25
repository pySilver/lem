"""What the review step reads from git besides the world: the change's size, its edits of Lem's
own settings files (`app/landing/review_edits.py`), the backlog folder at the base, and the
items the branch adds that `file` did not write (`land.due`, `land.careful`, `land.base_items`
and `land.branch_items` on `main`)."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import backlog, review_edits
from lem.model.landing import careful, review_due
from lem.records.base import Frozen
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from collections.abc import Iterable

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


def told(found: Iterable[BacklogItem]) -> Told:
    """Items as a reviewer is told of them."""
    return msgspec.convert(tuple(found), Told, from_attributes=True)


def gathered(context: Context) -> Gathered:
    """The facts of the change from origin's base to the worktree's tip."""
    git, worktree = context.ports.git, context.worktree
    span = (context.world.base, context.world.tip or "")
    stat = git.diff_stat(worktree, *span)
    written = {filed.path for filed in (context.record.landing or Landing()).filed}
    return Gathered(
        lines=stat.added + stat.removed,
        edits=review_edits.edits(git, worktree, span),
        at_base=backlog.files_at_base(git, worktree, *span),
        backlog=told(backlog.at_base(git, worktree, *span)),
        filed=told(
            found
            for found in backlog.added(git, worktree, *span)
            if found.path not in written
        ),
    )


def facts(context: Context, found: Gathered) -> review_due.Facts:
    """What `read --record` checks a review against."""
    checked = (context.record.landing or Landing()).checked
    paths = {one.path for one in checked.lowered} if checked else set()
    return review_due.Facts(
        careful=careful.reasons(context.record, found.edits),
        folder=backlog.FOLDER,
        at_base=found.at_base,
        lowered=tuple(sorted(paths)),
    )
