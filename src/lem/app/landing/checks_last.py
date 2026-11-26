"""How a task's last run of the checks ended, how long the workspace's last passed run took,
and where a run that holds the lock stands now (`land.ended_of`, `last_seconds`, `waits_of`
and `resumed_line` on `main`).

A run's length is its span of the checks, which begins after the gate and ends at its
`CheckEnd`; a red run stops before the serial commands, and would make the next run look
overdue, so only a passed one is a measure.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.model.landing import checks_said
from lem.records.base import Frozen, Moment
from lem.records.journal.landing import CheckEnd
from lem.store import survey

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

CHECKS = "checks"
SHORT = 9


class Ended(Frozen, frozen=True, kw_only=True):
    """The task's last run of the checks: when it ended, its tip, its result, how long it ran,
    its line, and the line for a session that did not start it."""

    at: Moment
    tip: str | None = None
    outcome: checks_said.Ending = msgspec.field(name="result")
    seconds: int | None = None
    say: str
    resumed: str


def seconds_of(record: Record, at: Moment) -> int | None:
    """How long the run that ended at `at` ran: its span of the checks."""
    spans = (span for span in record.task.spans if span.name == CHECKS)
    span = next((span for span in spans if span.end == at), None)
    if span is None:
        return None
    return int((at - span.start).total_seconds())


def ended_of(record: Record) -> Ended | None:
    """The task's newest end of the checks, as `--status` and `--stop` print it."""
    ends = [entry for entry in record.journal if isinstance(entry, CheckEnd)]
    if not ends:
        return None
    end = ends[-1]
    checked = record.landing.checked if record.landing else None
    return Ended(
        at=end.at,
        tip=None if checked is None else checked.tip[:SHORT],
        outcome=end.outcome,
        seconds=seconds_of(record, end.at),
        say=end.say,
        resumed=checks_said.resumed(record.task.slug, end.at, end.outcome),
    )


def last_seconds(state: Path) -> tuple[int | None, tuple[str, ...]]:
    """The length of the newest passed run of any task of the workspace, and the tasks whose
    record does not read, which the measure leaves out."""
    records, unread = survey.records(state)
    found = [timed for record in records for timed in passed_of(record)]
    return (max(found)[1] if found else None), unread


def passed_of(record: Record) -> list[tuple[Moment, int]]:
    """Each passed run of the task, when it ended and how long it took."""
    ends = (entry for entry in record.journal if isinstance(entry, CheckEnd))
    timed = (
        (end.at, seconds_of(record, end.at)) for end in ends if end.outcome == "passed"
    )
    return [(at, seconds) for at, seconds in timed if seconds is not None]
