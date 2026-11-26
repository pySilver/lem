"""Each entry of a task's journal in the feed's words, by its kind (`board_model.describe` on
`main`). An entry may be more than one row (a run of the checks is each command and its end) or
none (the end of a span its own entry says); the session entries are Lem's acts, which
`acts.py` reads."""

from typing import TYPE_CHECKING

from lem.board.views.activity import (
    tell_checks,
    tell_criteria,
    tell_decisions,
    tell_landing,
    tell_merge,
    tell_task,
    tell_work,
)
from lem.records.journal.landing import (
    CarefulMissed,
    CheckEnd,
    CheckWait,
    MergeWait,
    NotGreen,
    ReviewRound,
)
from lem.records.journal.merge import LandAgain, MergeNoted, ReadNoted, RefusalNoted
from lem.records.journal.task import (
    CriteriaNoted,
    DecisionNoted,
    OwnerAct,
    SpanMark,
    StateNoted,
    Summary,
)

if TYPE_CHECKING:
    from lem.board.views.activity.told import Told
    from lem.records.journal.entry import Entry
    from lem.records.task import Task


type Rows = tuple[Told, ...]


def told_of(entry: Entry, task: Task) -> Rows:
    """The rows of one entry of the task's journal."""
    found: tuple[Told, ...]
    match entry:
        case StateNoted():
            found = (tell_task.state(entry, task),)
        case SpanMark():
            found = with_origin(tell_work.span(entry, task), entry.carried_from)
        case DecisionNoted():
            found = with_origin(
                (tell_decisions.decision(entry, task),), entry.carried_from
            )
        case CriteriaNoted():
            found = with_origin((tell_criteria.criteria(entry),), entry.carried_from)
        case OwnerAct():
            found = (tell_task.owner(entry, task),)
        case Summary():
            found = (tell_task.summary(entry),)
        case _:
            found = landing_told(entry)
    return found


def with_origin(rows: Rows, origin: str | None) -> Rows:
    """Only copied rows name their predecessor."""
    if origin is None:
        return rows
    said = f"carried over from {origin}"
    return tuple(marked(row, said) for row in rows)


def marked(row: Told, said: str) -> Told:
    """Add where a copy came from after any detail of its own."""
    sub = " · ".join(part for part in (row.sub, said) if part)
    return row._replace(sub=sub)


def landing_told(entry: Entry) -> tuple[Told, ...]:
    """The rows of an entry of the landing."""
    found: Told
    match entry:
        case CheckEnd():
            return tell_checks.ended(entry)
        case ReviewRound():
            found = tell_landing.review(entry)
        case CarefulMissed():
            found = tell_landing.careful(entry)
        case NotGreen():
            found = tell_landing.not_green(entry)
        case CheckWait():
            found = tell_landing.check_wait(entry)
        case MergeWait():
            found = tell_landing.merge_wait(entry)
        case _:
            return merge_told(entry)
    return (found,)


def merge_told(entry: Entry) -> tuple[Told, ...]:
    """The rows of an entry of the merge; none for a session entry."""
    found: tuple[Told, ...]
    match entry:
        case ReadNoted():
            found = (tell_merge.read(entry),)
        case RefusalNoted():
            found = (tell_merge.refusal(entry),)
        case MergeNoted():
            found = (tell_merge.merged(entry),)
        case LandAgain():
            found = (tell_merge.again(entry),)
        case _:
            found = ()
    return found
