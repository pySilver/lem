"""A moment as text: the one place that writes Lem's three forms of a UTC time.

A record's form is its text, and a release reads the records of the one before it, so
each record keeps the form it was first written in. Three are in use: `stamp`,
`2026-11-24T10:18:18Z`, which the event log, the decisions, the landing and most
records write; `stamp_minute`, `2026-11-24T10:18Z`, the first word of a task's state
block; and `iso`, `2026-11-24T10:18:18+00:00`, which the board server's own files and
the notifications' and the Inbox's records write. Each takes the moment to write, a
`datetime` or seconds since the epoch; with none it writes now, read from
`datetime.now`, which `tests/clock/` moves for a test.

A moment that a caller got from elsewhere is written as it is: no zone is put on it or
taken off, so a caller that holds a moment in another zone converts it first, as it did
before this file. The hooks keep their own lines (`corrections.py`, `session_hook.py`),
since a hook loads no module it does not need. It imports nothing of Lem's.
"""

from datetime import UTC, datetime

SECONDS = "%Y-%m-%dT%H:%M:%SZ"
MINUTES = "%Y-%m-%dT%H:%MZ"


def moment_of(moment: datetime | float | None) -> datetime:
    """MOMENT as a `datetime`: a number is seconds since the epoch, in UTC; None is
    now."""
    if moment is None:
        return datetime.now(UTC)
    # a number is told from a datetime, never the other way: the class `tests/clock/`
    # puts in datetime's place is not the class of a moment made before it
    if isinstance(moment, int | float):
        return datetime.fromtimestamp(moment, UTC)
    return moment


def stamp(moment: datetime | float | None = None) -> str:
    """MOMENT, or now, to the second: `2026-11-24T10:18:18Z`."""
    return moment_of(moment).strftime(SECONDS)


def stamp_minute(moment: datetime | float | None = None) -> str:
    """MOMENT, or now, to the minute: `2026-11-24T10:18Z`."""
    return moment_of(moment).strftime(MINUTES)


def iso(moment: datetime | float | None = None) -> str:
    """MOMENT, or now, to the second with its offset: `2026-11-24T10:18:18+00:00`."""
    return moment_of(moment).isoformat(timespec="seconds")
