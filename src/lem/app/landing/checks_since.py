"""Where a run of the checks that holds the lock stands now (`land.checks_status` and
`waits_of` on `main`): its commands run since its span of the checks began, or it waits at the
gate, as `checks-wait.json` says."""

from typing import TYPE_CHECKING

from lem.app.landing import checks_last, checks_waits
from lem.records.base import Frozen, Moment
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record
    from lem.records.work import Span

CHECKS = "checks"


class Running(Frozen, frozen=True, kw_only=True):
    """A run that holds the lock: since when it runs (or waits), for how many seconds its
    commands run, its wait at the gate, and the workspace's last passed run in seconds."""

    since: Moment
    seconds: int | None = None
    waits: checks_waits.Waited | None = None
    last: int | None = None


def running(record: Record, state: Path, since: Moment, now: Moment) -> Running:
    """Where the run that holds the lock since `since` stands: its commands run since its
    span began, or it waits at the gate."""
    last = checks_last.last_seconds(state)
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
