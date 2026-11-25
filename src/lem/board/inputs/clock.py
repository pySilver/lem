"""A moment of a record as the board prints it: a length (`45s`, `3m 07s`, `25m`, `2h 05m`,
`3d 4h`), a time since (`just now`, `32m ago`), and a clock time with its date when it is not
the day of the page (`15:40`, `Nov 24 23:50`), in the zone the board shows.

The rule is `main`'s `board_model.span`, `ago` and `stamp`; the moment of the page and the zone
come in as arguments, so the same records print the same words in a test.
"""

from typing import TYPE_CHECKING

from lem.board.inputs.parts import When

if TYPE_CHECKING:
    from datetime import datetime, tzinfo

    from lem.board.inputs.text import Plain

# Up to this many minutes a length keeps its seconds (`9m 59s`), and up to this many hours its
# minutes (`47h 59m`); `main`'s SECONDS_SHOWN_M and HOURS_SHOWN_H.
SECONDS_SHOWN = 10
HOURS_SHOWN = 48
# A time since shorter than this is `just now` (`main`'s JUST_NOW_MS).
JUST_NOW = 5


def length(seconds: float) -> str:
    """A length of time as the board says it."""
    whole = max(0, round(seconds))
    minutes, rest = divmod(whole, 60)
    if not minutes:
        return f"{whole}s"
    if minutes < SECONDS_SHOWN:
        padded = str(rest).rjust(2, "0")
        return f"{minutes}m {padded}s"
    return hours_of(minutes)


def hours_of(minutes: int) -> str:
    """A length of ten minutes or more: `25m`, `2h 05m`, `3d 4h`."""
    hours, past = divmod(minutes, 60)
    if not hours:
        return f"{minutes}m"
    if hours < HOURS_SHOWN:
        padded = str(past).rjust(2, "0")
        return f"{hours}h {padded}m"
    days, left = divmod(hours, 24)
    return f"{days}d {left}h"


def ago(seconds: float) -> str:
    """The time since a moment, as the board says it."""
    if seconds < JUST_NOW:
        return "just now"
    return f"{length(seconds)} ago"


def stamp(moment: datetime, now: datetime, zone: tzinfo) -> str:
    """The clock time of `moment` in `zone`, with its date before it when it is not the day of
    `now` there, so that 00:10 and 23:50 do not read as one evening."""
    here = moment.astimezone(zone)
    clock = here.strftime("%H:%M")
    if here.date() == now.astimezone(zone).date():
        return clock
    month = here.strftime("%b")
    return f"{month} {here.day} {clock}"


def since(moment: datetime, now: datetime, title: Plain | None = None) -> When:
    """The length from `moment` to now, which the browser's clock moves on."""
    shown = length((now - moment).total_seconds())
    return When(at=moment, shown=shown, title=title, ticks="since")


def gone(moment: datetime, now: datetime, title: Plain | None = None) -> When:
    """The time since `moment`, which the browser's clock moves on (`32m ago`)."""
    shown = ago((now - moment).total_seconds())
    return When(at=moment, shown=shown, title=title, ticks="ago")


def fixed(
    moment: datetime, now: datetime, zone: tzinfo, title: Plain | None = None
) -> When:
    """The clock time of `moment`, which stays as it is."""
    return When(at=moment, shown=stamp(moment, now, zone), title=title)
