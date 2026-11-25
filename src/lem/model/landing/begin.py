"""The record a start writes: the round begun, the task `landing`, and for an open task's new
round its count and its journal entry; or the block of a task whose project names no command of
the checks (`land.start_locked` on `main`)."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.landing.start_said import NO_CHECKS
from lem.records.holds import Blocked
from lem.records.journal.merge import LandAgain
from lem.records.journal.task import StateNoted
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.records.base import Moment
    from lem.records.landing.start import Started
    from lem.records.record import Record


def again(landing: Landing, started: Started) -> Landing:
    """An open task's landing in a new round: counted, back in `preparing`, and with no
    resolution of a conflict of a round before."""
    return replace(
        landing,
        round=started.round,
        relands=landing.relands + 1,
        phase="preparing",
        started=started,
        resolution=None,
    )


def line_of(record: Record, started: Started) -> str:
    """The line of the task's move to `landing`."""
    if started.conflicting:
        return "the forge calls the pull request conflicting: the branch goes onto the base"
    if (record.landing or Landing()).phase == "open":
        return "the base moved: the checks run again"
    return "the checks start"


def begun(record: Record, started: Started) -> Record:
    """The record with the round begun, the task `landing` and unblocked; a new round of an
    open task is counted and noted."""
    landing = record.landing or Landing()
    entries = (
        StateNoted(at=started.at, status="landing", line=line_of(record, started)),
    )
    if landing.phase == "open":
        landing = again(landing, started)
        counted = LandAgain(
            at=started.at,
            round=started.round,
            relands=landing.relands,
            conflicting=started.conflicting,
        )
        entries = (counted, *entries)
    else:
        landing = replace(landing, started=started)
    task = replace(record.task, status="landing", since=started.at, hold=None)
    journal = (*record.journal, *entries)
    return replace(record, task=task, landing=landing, journal=journal)


def blocked(record: Record, refusal: Refusal, now: Moment) -> Record:
    """The record of a task that `start` blocked for want of a command of the checks; a task
    blocked so already is left as it is."""
    if is_blocked(record):
        return record
    made = Blocked(why=NO_CHECKS, fix=refusal.fix, since=now)
    entry = StateNoted(
        at=now, status=record.task.status, hold="blocked", line=refusal.why
    )
    task = replace(record.task, hold=made)
    return replace(record, task=task, journal=(*record.journal, entry))


def is_blocked(record: Record) -> bool:
    """Whether `start` blocked the task already for want of a command of the checks."""
    hold = record.task.hold
    return isinstance(hold, Blocked) and hold.why == NO_CHECKS
