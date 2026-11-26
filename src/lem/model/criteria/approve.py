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
from lem.model.criteria import approvers, clear, digest, skip, waits, yes
from lem.model.criteria.read import Sheet
from lem.records import approvals, base
from lem.records.journal.task import CriteriaNoted

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.records.criteria import Criteria
    from lem.records.criterion import Criterion
    from lem.records.record import Record
    from lem.records.task import Task

# Who ends the wait for the owner's yes: his yes, and an approval without him.
ENDS_WAIT = frozenset(("owner", "alone"))


class Asked(base.Frozen, frozen=True, kw_only=True):
    """An approval asked for: by whom, of which criteria, whether the task runs without the
    owner now, why its request is not his own sentence (None when it is), whether the
    criteria may carry the lead's test lines (the plan's own), and for his yes the question
    his page showed, where he gave it, and the mark of the bytes it showed."""

    by: approvals.ApprovedBy
    sheet: Sheet
    alone: bool = False
    other: str | None = None
    plan: bool = False
    question: str | None = None
    via: yes.Via = "session"
    shown: str | None = None


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
    return approvers.first_contract(task, by) or clear.clear(task, marked)


def untested_criterion(criterion: Criterion) -> Criterion:
    """A criterion as an approval keeps it: with its case and chart, and no test line."""
    return replace(criterion, tests=(), no_test=None)


def approval_of(task: Task, asked: Asked, now: base.Moment) -> approvals.Approval:
    """The approval `asked`, numbered after the task's last one."""
    sheet = asked.sheet
    kept = tuple(untested_criterion(one) for one in sheet.criteria)
    before = task.criteria.approvals
    return approvals.Approval(
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


def recorded(task: Task, sheet: Sheet, approval: approvals.Approval) -> Criteria:
    """What the task knows of its criteria after `approval` of the criteria `sheet`: the first
    approval of the owner, or one without him, after their newest wait ends it."""
    criteria = task.criteria
    wait = criteria.waited
    if wait is not None and wait.ended_by is None and approval.by in ENDS_WAIT:
        wait = replace(wait, ended_by=approval.number)
    return replace(
        criteria,
        waited=wait,
        size=sheet.size,
        why=sheet.why,
        criteria=sheet.criteria,
        how=sheet.how,
        digest=sheet.digest,
        approvals=(*criteria.approvals, approval),
        skip_approval=skip.approval_of(task, approval),
    )


def approved(
    record: Record,
    *,
    asked: Asked,
    now: base.Moment,
    answer: Callable[[Record], Record] | None = None,
) -> Record:
    """The approval and its answer in one record, after the rules of who approves."""
    if answer is not None:
        record = answer(record)
    task = record.task
    yes.page_of(task, asked.question)
    refusal = refusal_of(task, asked)
    if refusal is not None:
        raise refusal
    if answer is None and asked.by in ENDS_WAIT:
        task = yes.answered_yes(task, asked.via, asked.shown, now)
    approval = approval_of(task, asked, now)
    noted = CriteriaNoted(
        at=now,
        event="approved",
        by=approval.by,
        number=approval.number,
        size=approval.size,
    )
    task = replace(
        task,
        criteria=recorded(task, asked.sheet, approval),
        hold=waits.hold_after(task, ends=asked.by in ENDS_WAIT),
    )
    return replace(record, task=task, journal=(*record.journal, noted))
