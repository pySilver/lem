"""The line that says the criteria are not the ones the personas read, and what changed them
(`main:land.unread`): an approval of the owner's after the read that holds other criteria, or a
change of the build."""

from typing import TYPE_CHECKING

from lem.model.criteria import digest
from lem.model.landing import propose_criteria
from lem.records.decisions import CriterionChanged

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.landing.pr_inputs import Lines
    from lem.records.approvals import Approval, PersonaRead
    from lem.records.record import Record
    from lem.records.task import Task

UNREAD = (
    "- the criteria changed after the personas' read{0}, and the change was not read"
)


def changers(task: Task, read: PersonaRead) -> list[str]:
    """What changed the criteria after a read: the owner's newest approval after it that
    holds other criteria, and a change of the build."""
    ended = read.ended or read.started
    his = [one.number for one in task.criteria.approvals if other(one, read, ended)]
    what = [f"by the owner's approval {number}" for number in his[-1:]]
    changes = (one for one in task.decisions if isinstance(one, CriterionChanged))
    if any(change.at >= ended for change in changes):
        what.append("by a change of the build")
    return what


def other(approval: Approval, read: PersonaRead, ended: datetime) -> bool:
    """Whether an approval of the owner's after a read holds other criteria than it read."""
    later = approval.by == "owner" and approval.at >= ended
    return later and approval.digest != read.digest


def unread(record: Record) -> Lines:
    """The line that says the criteria are not the ones the personas read, and what changed
    them."""
    task = record.task
    read = propose_criteria.newest(task)
    if read is None or not read.answered or text_mark(task) == read.digest:
        return ()
    what = " and ".join(changers(task, read))
    named = f", {what}" if what else ""
    return (UNREAD.format(named),)


def text_mark(task: Task) -> str | None:
    """Compare the read to the criteria's text. The check digest includes the tests."""
    kept = task.criteria
    return None if kept.size is None else digest.of_texts(kept.size, kept.criteria)
