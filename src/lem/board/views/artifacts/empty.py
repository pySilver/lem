"""The gray line of a section of a task's map that holds no document (`board_task.empty_reason`
on `main`): what a tab of the board shows instead, not yet, or none, by the task's track and
where it stands; for a pruned task, that its rows went into its summary."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views.artifacts import before, landed
from lem.records.journal.task import Summary

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.records.record import Record

# The sections whose rows went with a pruned task's journal into its summary.
SUMMED = frozenset(("criteria", "checks", "review", "pr"))
REASONS: MappingProxyType[str, Callable[[Record], str]] = MappingProxyType(
    {
        "criteria": before.criteria,
        "plan": before.plan,
        "build": before.build,
        "checks": landed.checks,
        "review": landed.review,
        "pr": landed.proposal,
    }
)


def summed(record: Record, key: str) -> str:
    """The line of a section of a pruned task, whose rows went into its summary."""
    summary = next(
        (entry for entry in record.journal if isinstance(entry, Summary)), None
    )
    proposed = (record.landing or landed.NO_LANDING).proposed
    if key == "pr" and (proposed or (summary and summary.green is not None)):
        return "no document: green or not green is on the Overview"
    return "no document: what showed it went with the events, into one summary"


def empty_reason(record: Record, key: str) -> str:
    """The line of the section `key` of the task's map when it holds no document."""
    if key == "request":
        return "none: the request was typed in a session"
    pruned = any(isinstance(entry, Summary) for entry in record.journal)
    if pruned and key in SUMMED:
        return summed(record, key)
    return REASONS[key](record)
