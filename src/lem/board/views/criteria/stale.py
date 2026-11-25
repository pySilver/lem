"""Whether the personas' read is of the criteria as they stand (`board_model.read_stale` on
`main`, as `land.unread` says it): when it is not, what changed them after it, an approval of the
owner's with other criteria or a change of the build."""

from typing import TYPE_CHECKING

from lem.model.criteria import digest
from lem.model.decisions.changes import changes_of

if TYPE_CHECKING:
    from lem.records.approvals import PersonaRead
    from lem.records.task import Task


def standing_mark(task: Task) -> str | None:
    """The mark of the criteria as they stand: the newest approval's, or, after a change of
    the build, the mark of an approval of the same texts; None when none has them."""
    found = changes_of(task)
    if found.approved is None or not found.changes:
        return found.approved.digest if found.approved else None
    expected = [" ".join(text.split()) for text in found.expected or ()]
    same = (
        one.digest
        for one in reversed(task.criteria.approvals)
        if digest.flat(one.criteria) == expected
    )
    return next(same, None)


def read_stale(task: Task, read: PersonaRead) -> str:
    """What changed the criteria after the read, or "" when it read them as they stand."""
    if not task.criteria.approvals or standing_mark(task) == read.digest:
        return ""
    said = " and".join(causes_of(task, read))
    return f"The criteria changed after this read{said}, and the change was not read."


def causes_of(task: Task, read: PersonaRead) -> list[str]:
    """What changed the criteria after the read: an approval of the owner's with other
    criteria, a change of the build."""
    moment = read.ended or read.started
    his = [
        one.number
        for one in task.criteria.approvals
        if one.by == "owner" and one.at > moment and one.digest != read.digest
    ]
    history = changes_of(task).history
    causes = [f" by your approval {number}" for number in his[-1:]]
    if any(one.change.at > moment for one in history):
        causes.append(" by a change of the build")
    return causes
