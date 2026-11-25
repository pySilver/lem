"""The lines of the sections of a task's map before its landing, when they hold no document:
the criteria, the plan and the build (`board_task.empty_reason` on `main`)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.record import Record

ENDED = frozenset(("landed", "answered", "dropped"))


def ended(record: Record) -> str:
    """The line of a section that a task which ended has nothing in."""
    status = record.task.status
    if status == "answered":
        return "none: it ended with a report"
    if status == "dropped":
        return "none: the task was dropped"
    return "none"


def either(record: Record, there: str | None, waits: str) -> str:
    """`there` when the tab shows it, the end's line when the task ended, else `waits`."""
    if there:
        return there
    return ended(record) if record.task.status in ENDED else waits


def criteria(record: Record) -> str:
    """The criteria's section."""
    known = record.task.criteria
    there = known.approvals or known.criteria
    shown = "no document: Criteria and decisions shows them" if there else None
    return either(record, shown, "not yet: the interview writes them")


def plan(record: Record) -> str:
    """The plan's section."""
    task = record.task
    shape = task.shape
    if task.lead == "small" or (shape is not None and shape.track == "small"):
        return "no plan: the fast track"
    return either(record, None, "not yet: the lead writes it")


def build(record: Record) -> str:
    """The build's section."""
    landing = record.task.status in {"ready", "landing", "open"}
    return ended(record) if landing else either(record, None, "not yet: the build runs")
