"""The changes of a task's approved criteria in the build, and the criteria they give
(`decisions.Task.changes` and `applied` on `main`).

An approval is known by its number, not by its text: one of a text approved before is still a new
one. The expected criteria are the newest approval's with the changes recorded after it, in
order. Every change stays in the history, each with the approval it applied to and, when an
approval of the owner's came after it, that approval's number: his approval made the change his.
A task with no approved criteria has no changes: its plan's criteria are their one source.
"""

from typing import TYPE_CHECKING

from lem.model.decisions import applied
from lem.records.base import Frozen, Moment
from lem.records.decisions import CriterionChanged

if TYPE_CHECKING:
    from lem.records.approvals import Approval
    from lem.records.task import Task


class Approved(Frozen, frozen=True, kw_only=True):
    """An approval as the changes name it: its number, moment, who gave it, size and mark."""

    number: int
    at: Moment
    by: str
    size: str
    digest: str


class Past(Frozen, frozen=True, kw_only=True):
    """A change of the history, and the owner's approval that took it over, if one did."""

    change: CriterionChanged
    taken_over_by: int | None = None


class Changes(Frozen, frozen=True, kw_only=True):
    """The approvals, the changes of the newest one in order, every change with what took it
    over, and the expected criteria (None with no approval)."""

    approved: Approved | None = None
    approvals: tuple[Approved, ...] = ()
    changes: tuple[CriterionChanged, ...] = ()
    history: tuple[Past, ...] = ()
    expected: tuple[str, ...] | None = None


def summary(approval: Approval) -> Approved:
    """An approval as the changes name it."""
    return Approved(
        number=approval.number,
        at=approval.at,
        by=approval.by,
        size=approval.size,
        digest=approval.digest,
    )


def past(change: CriterionChanged, approvals: tuple[Approval, ...]) -> Past:
    """A change with the owner's approval after the one it applied to, if one came."""
    later = (
        one.number
        for one in approvals
        if one.number > change.approval and one.by == "owner"
    )
    return Past(change=change, taken_over_by=next(later, None))


def changes_of(task: Task) -> Changes:
    """The changes of the task's approved criteria, and the criteria they give."""
    approvals = task.criteria.approvals
    if not approvals:
        return Changes()
    newest = approvals[-1]
    every = tuple(one for one in task.decisions if isinstance(one, CriterionChanged))
    current = tuple(one for one in every if one.approval == newest.number)
    return Changes(
        approved=summary(newest),
        approvals=tuple(summary(one) for one in approvals),
        changes=current,
        history=tuple(past(one, approvals) for one in every),
        expected=applied.expected_of(newest, current),
    )
