"""The fast track's criterion in the pull request's text (`main:land.small_text`): the track
and why, who approved it when it was not the owner, the criterion with what its tests gave, and
each change of it during the build."""

from typing import TYPE_CHECKING

from lem.app.landing.pr_criteria import NO_REASON, change_line, criterion_lines
from lem.app.landing.pr_inputs import Block
from lem.model.landing.green_words import reason
from lem.records.decisions import CriterionChanged

if TYPE_CHECKING:
    from lem.records.record import Record

UNREAD = "the personas did not read it."


def approved_by(record: Record) -> str:
    """Who approved the criterion when it was not the owner, and that no persona read it."""
    approvals = record.task.criteria.approvals
    newest = approvals[-1] if approvals else None
    if newest is None or newest.by not in {"lem", "alone"}:
        return ""
    day = newest.at.date().isoformat()
    if newest.by == "lem":
        return f" Lem approved it in the owner's name on {day}; {UNREAD}"
    opened = (
        "the night opened the task"
        if record.task.night
        else "someone else wrote the request"
    )
    return f" Lem approved it on {day} without the owner ({opened}); {UNREAD}"


def criterion(record: Record) -> tuple[Block, ...]:
    """The fast track's criterion block."""
    task = record.task
    why = reason(task.criteria.why or NO_REASON)
    found = tuple(
        line for one in task.criteria.criteria for line in criterion_lines(record, one)
    )
    changes = tuple(
        change_line(record, change)
        for change in task.decisions
        if isinstance(change, CriterionChanged)
    )
    track = f"The fast track, because {why}.{approved_by(record)}"
    return (
        Block(
            heading="## The acceptance criterion", lines=(track, "", *found, *changes)
        ),
    )
