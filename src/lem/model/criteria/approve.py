"""An approval of a task's criteria: the checks of who approves, and the record after it
(`criteria.cmd_approve` on `main`).

Each approval is a new one, with a number of its own, also of a text approved before; it keeps
the criteria word for word, each with its case and chart and with no test line, their mark, and
the approval it replaces. The owner's yes, and an approval without him, end the wait of the
criteria for his yes.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.criteria import approvers, digest, reads, waits
from lem.model.criteria.read import Sheet
from lem.records.approvals import Approval, ApprovedBy
from lem.records.base import Frozen

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.criteria import Criteria
    from lem.records.criterion import Criterion
    from lem.records.record import Record
    from lem.records.task import Task

# Who ends the wait for the owner's yes: his yes, and an approval without him.
ENDS_WAIT = frozenset(("owner", "alone"))


class Asked(Frozen, frozen=True, kw_only=True):
    """An approval asked for: by whom, of which criteria, whether the task runs without the
    owner now, why its request is not his own sentence (None when it is), and whether the
    criteria may carry the lead's test lines (the plan's own)."""

    by: ApprovedBy
    sheet: Sheet
    alone: bool = False
    other: str | None = None
    plan: bool = False


def untested(asked: Asked) -> Refusal | None:
    """The criteria the owner approves have no test line: the lead adds them in the plan."""
    tested = [one.number for one in asked.sheet.criteria if one.tests or one.no_test]
    if not tested or asked.plan:
        return None
    return Refusal(
        "test-lines",
        f"criterion {tested[0]} has a test line, and the criteria the owner approves have "
        "none",
        "take the test lines out: the lead adds them in the plan",
    )


def refusal_of(task: Task, asked: Asked) -> Refusal | None:
    """Why the approval `asked` may not be made now, or None."""
    by, sheet = asked.by, asked.sheet
    said: Refusal | None = None
    if by in ENDS_WAIT:
        said = approvers.no_on_record(task, owner=by == "owner")
    said = said or untested(asked)
    if said or by == "owner":
        return said
    if by == "lem":
        return approvers.by_lem(task, sheet, asked.other, alone=asked.alone)
    if by == "alone":
        return approvers.by_alone(task, sheet, asked.other, alone=asked.alone)
    marked = digest.of_texts(sheet.size, sheet.criteria)
    return approvers.first_contract(task, by) or reads.clear(task, marked)


def untested_criterion(criterion: Criterion) -> Criterion:
    """A criterion as an approval keeps it: with its case and chart, and no test line."""
    return replace(criterion, tests=(), no_test=None)


def approval_of(task: Task, asked: Asked, now: datetime) -> Approval:
    """The approval `asked`, numbered after the task's last one."""
    sheet = asked.sheet
    kept = tuple(untested_criterion(one) for one in sheet.criteria)
    before = task.criteria.approvals
    return Approval(
        number=len(before) + 1,
        at=now,
        by=asked.by,
        size=sheet.size,
        why=sheet.why,
        digest=digest.of_texts(sheet.size, kept),
        criteria=kept,
        how=sheet.how,
        replaces=before[-1].number if before else None,
    )


def recorded(criteria: Criteria, sheet: Sheet, approval: Approval) -> Criteria:
    """What the task knows of its criteria after `approval` of the criteria `sheet`."""
    return replace(
        criteria,
        size=sheet.size,
        why=sheet.why,
        criteria=sheet.criteria,
        how=sheet.how,
        digest=sheet.digest,
        approvals=(*criteria.approvals, approval),
    )


def approved(record: Record, *, asked: Asked, now: datetime) -> Record:
    """The record with the approval `asked`; refused by the rules of who approves."""
    task = record.task
    refusal = refusal_of(task, asked)
    if refusal is not None:
        raise refusal
    approval = approval_of(task, asked, now)
    criteria = recorded(task.criteria, asked.sheet, approval)
    hold = waits.hold_after(task, ends=asked.by in ENDS_WAIT)
    return replace(record, task=replace(task, criteria=criteria, hold=hold))
