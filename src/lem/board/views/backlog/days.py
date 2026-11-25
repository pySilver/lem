"""How old a backlog item is, from the day of its `added` (`board_pages.days_old` on
`main`)."""

import re
from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import tzinfo

DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
SECONDS_A_DAY = 86400
# An item's day counts from its noon, which is that day on any clock from UTC-11 to UTC+11.
NOON = time.fromisoformat("12:00")


def days_old(added: str | None, now: datetime, zone: tzinfo) -> int | None:
    """How many days before `now` the item was added, from the noon of its day in the
    board's zone; None for no day."""
    day = day_of(added)
    if day is None:
        return None
    noon = datetime.combine(day, NOON, zone)
    seconds = (now - noon.astimezone(UTC)).total_seconds()
    return max(0, round(seconds / SECONDS_A_DAY))


def day_of(added: str | None) -> date | None:
    """The day of an item's `added`, or None when it names no day."""
    if added is None or not DAY.fullmatch(added):
        return None
    try:
        return date.fromisoformat(added)
    except ValueError:
        return None
