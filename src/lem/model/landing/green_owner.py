"""The reasons of green that the owner's absence gives (`main:land.not_green`): criteria
nobody approved or approved without him, and each decision of his taken past the personas or
left unsettled."""

from typing import TYPE_CHECKING

from lem.model.landing import green_words
from lem.records.decisions import Taken

if TYPE_CHECKING:
    from lem.records.task import Task

UNSETTLED = "the lead's pick, which no level of the ladder settled"


def approval(task: Task) -> tuple[str, ...]:
    """The reason of the approval: none, or the newest made without him."""
    approvals = task.criteria.approvals
    if not approvals:
        return ("nobody approved the criteria",)
    newest = approvals[-1]
    if newest.by != "alone":
        return ()
    someone = task.shape is not None and task.shape.someone_else
    if task.mode == "alone" or not someone:
        how = "while the task ran without the owner"
    else:
        how = "without the owner, since someone else wrote the request"
    day = newest.at.date().isoformat()
    return (
        f"the owner did not approve the criteria: they were approved on {day} {how}",
    )


def decided(decision: Taken) -> str:
    """A decision of his taken without him, as a reason."""
    taken = green_words.taken_by(decision)
    who = UNSETTLED if decision.unsettled else f"by {taken}"
    what = f'({decision.what}): "{decision.chose}"'
    return f"decision {decision.id} was taken without the owner {what}, {who}"


def decisions(task: Task) -> tuple[str, ...]:
    """Each decision of his taken past the personas or left unsettled."""
    return tuple(
        decided(decision)
        for decision in task.decisions
        if isinstance(decision, Taken) and green_words.without_him(decision)
    )
