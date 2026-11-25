"""How a task's last run of the checks ended, how long the workspace's last passed run took,
and where a run that holds the lock stands now (`land.ended_of`, `last_seconds`, `waits_of`
and `resumed_line` on `main`).

A run's length is its span of the checks, which begins after the gate and ends at its
`CheckEnd`; a red run stops before the serial commands, and would make the next run look
overdue, so only a passed one is a measure.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import checks_waits
from lem.model.landing import checks_said
from lem.records.base import Frozen, Moment
from lem.records.journal.landing import CheckEnd
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record
    from lem.records.work import Span

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


class Running(Frozen, frozen=True, kw_only=True):
    """A run that holds the lock: since when it runs (or waits), for how many seconds its
    commands run, its wait at the gate, and the workspace's last passed run in seconds."""

    since: Moment
    seconds: int | None = None
    waits: checks_waits.Waited | None = None
    last: int | None = None


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


def last_seconds(state: Path) -> int | None:
    """The length of the newest passed run of any task of the workspace."""
    found: list[tuple[Moment, int]] = []
    for record in tasks.every(state):
        ended = ended_of(record)
        if (
            ended is not None
            and ended.outcome == "passed"
            and ended.seconds is not None
        ):
            found.append((ended.at, ended.seconds))
    return max(found)[1] if found else None


def running(record: Record, state: Path, since: Moment, now: Moment) -> Running:
    """Where the run that holds the lock since `since` stands: its commands run since its
    span began, or it waits at the gate."""
    last = last_seconds(state)
    span = open_span(record, since)
    if span is not None:
        seconds = int((now - span.start).total_seconds())
        return Running(since=span.start, seconds=seconds, last=last)
    waits = checks_waits.read(places.task_folder(state, record.task.slug))
    fresh = waits if waits is not None and waits.at >= since else None
    return Running(since=since, waits=fresh, last=last)


def open_span(record: Record, since: Moment) -> Span | None:
    """The span of the checks that began at `since` or after and has not ended."""
    spans = [span for span in record.task.spans if span.name == CHECKS]
    span = spans[-1] if spans else None
    if span is None or span.end is not None or span.start < since:
        return None
    return span
