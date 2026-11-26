"""Where a run of the checks that holds the lock stands now (`land.checks_status` and
`waits_of` on `main`): its commands run since its span of the checks began, or it waits at the
gate, as its journal says."""

from typing import TYPE_CHECKING

from lem.app.landing import checks_last, checks_waits
from lem.records.base import Frozen, Moment

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record
    from lem.records.work import Span
    from lem.store.steps import Holder

CHECKS = "checks"


class Running(Frozen, frozen=True, kw_only=True):
    """A run that holds the lock: since when it runs (or waits), for how many seconds its
    commands run, its wait at the gate, and the workspace's last passed run in seconds."""

    since: Moment
    seconds: int | None = None
    waits: checks_waits.Waited | None = None
    last: int | None = None


def running(record: Record, state: Path, holder: Holder, now: Moment) -> Running:
    """Where the run that holds the lock stands: its commands run since its
    span began, or it waits at the gate."""
    last = checks_last.last_seconds(state)
    waits = checks_waits.latest(record.journal, holder.run)
    if waits is not None:
        return Running(since=holder.since, waits=waits, last=last)
    span = open_span(record, holder.since)
    if span is not None:
        seconds = int((now - span.start).total_seconds())
        return Running(since=span.start, seconds=seconds, last=last)
    return Running(since=holder.since, last=last)


def open_span(record: Record, since: Moment) -> Span | None:
    """The span of the checks that began at `since` or after and has not ended."""
    spans = [span for span in record.task.spans if span.name == CHECKS]
    span = spans[-1] if spans else None
    if span is None or span.end is not None or span.start < since:
        return None
    return span
