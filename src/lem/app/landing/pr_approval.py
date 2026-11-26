"""The criteria's approval and the wait it ended, in the pull request's checks."""

from typing import TYPE_CHECKING

from lem.model.landing.propose_criteria import HIS

if TYPE_CHECKING:
    from lem.records.approvals import Approval
    from lem.records.base import Moment
    from lem.records.task import Task

STAMP = "%Y-%m-%d %H:%M UTC"
OWNER = "owner"


def ended_by(approvals: tuple[Approval, ...], number: int | None) -> Approval | None:
    """The approval that ended the newest wait, which a later approval does not replace."""
    return next(
        (one for one in approvals if one.number == number and one.by in HIS),
        None,
    )


def dated(approval: Approval | None) -> str:
    """The date and actor of an approval that counts as an answer to the owner."""
    if approval is None or approval.by not in HIS:
        return ""
    day = approval.at.date().isoformat()
    if approval.by == OWNER:
        return f"the owner approved them on {day}"
    return f"approved on {day} while the task ran without the owner"


def answered(end: Approval) -> str:
    """The approval that ended the wait with its time and actor."""
    when = end.at.strftime(STAMP)
    if end.by == OWNER:
        return f"the owner gave it on {when}"
    return (
        f"the wait ended without the owner: approved on {when} "
        "while the task ran without the owner"
    )


def waited(since: Moment, end: Approval, newest: Approval) -> str:
    """When the wait began, what ended it and whether the owner approved it again."""
    began, answer = since.strftime(STAMP), answered(end)
    line = f"the criteria waited for the owner's yes from {began}, and {answer}"
    if newest.by != OWNER or newest.number == end.number:
        return line
    again = "again " if end.by == OWNER else ""
    day = newest.at.date().isoformat()
    return f"{line}; the owner approved them {again}on {day}"


def approved(task: Task) -> str:
    """The wait and its answer when recorded, or the latest approval's date."""
    approvals = task.criteria.approvals
    if not approvals:
        return ""
    wait = task.criteria.waited
    newest = approvals[-1]
    if wait is not None:
        end = ended_by(approvals, wait.ended_by)
        if end is not None:
            return waited(wait.since, end, newest)
    return dated(newest)
