"""How an item, a verdict and the list name one proposal: `retro of 2026-11-23 #3`, its run's
kind, its day and its number in that day's record."""

import datetime as dt
import re

from lem.addons.proposals.record import Kind
from lem.records.base import Frozen

PATTERN = re.compile(r"(retro|night) of (\d{4}-\d{2}-\d{2}) #([1-9]\d*)")


class Named(Frozen, frozen=True, kw_only=True):
    """One proposal by its name: its kind, its day and its number."""

    kind: Kind
    day: dt.date
    number: int


def name_of(kind: Kind, day: dt.date, number: int) -> str:
    """The name of proposal `number` of the `kind`'s record of `day`."""
    return f"{kind} of {day.isoformat()} #{number}"


def parsed(text: str) -> Named | None:
    """The proposal `text` names, or None for a text that is no such name or no such day."""
    found = PATTERN.fullmatch(text.strip())
    if found is None:
        return None
    kind: Kind = "retro" if found[1] == "retro" else "night"
    try:
        day = dt.date.fromisoformat(found[2])
    except ValueError:
        return None
    return Named(kind=kind, day=day, number=int(found[3]))
