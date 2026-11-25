"""A moment of Lem: UTC, to the second.

A record holds a `datetime`, which msgspec writes as `2026-11-24T10:18:18Z`. The moment is read
here once, by the command or the duty that acts, and comes into every rule as an argument.
"""

from datetime import UTC, datetime

MINUTES = "%Y-%m-%dT%H:%MZ"


def now() -> datetime:
    """Now, in UTC, to the second: a record's moment carries no fraction."""
    return datetime.now(UTC).replace(microsecond=0)


def minute(moment: datetime) -> str:
    """`2026-11-24T10:18Z`: the moment as the board and a line for the owner show it."""
    return moment.astimezone(UTC).strftime(MINUTES)


def compact(moment: datetime) -> str:
    """`20261124T101818Z`: the moment in a name, where a colon may not stand."""
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
