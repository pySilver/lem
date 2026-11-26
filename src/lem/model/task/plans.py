"""The name of a task's plan file, and the plan a task has (`plans.py` on `main`).

`[paths] plan_file` is a pattern of the tokens `YYYY`, `MM` and `DD`, the day the plan was
written, and `<slug>`, the task's. A task resumed from another works on a branch cut from the old
one's tip, so its plan is the old task's file until its lead writes one of its own name.
"""

import re
from datetime import date
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Iterable

    from lem.records.record import Record

PLAN_FILE = "YYYY-MM-DD-<slug>.md"
SLUG = "<slug>"
TOKENS = MappingProxyType(
    {
        "YYYY": r"(?P<Y>\d{4})",
        "MM": r"(?P<M>\d{2})",
        "DD": r"(?P<D>\d{2})",
        SLUG: r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)",
    }
)
TOKEN = re.compile(r"YYYY|MM|DD|<slug>")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
DAY_KEYS = ("Y", "M", "D")

type Slugs = tuple[str, ...]


def regex(pattern: str, slug: str | None) -> re.Pattern[str]:
    """The names a pattern gives the plan of `slug` on any day, or of any task with None."""
    parts: list[str] = []
    at = 0
    for found in TOKEN.finditer(pattern):
        parts.append(re.escape(pattern[at : found.start()]))
        parts.append(token_form(found.group(), slug))
        at = found.end()
    parts.append(re.escape(pattern[at:]))
    return re.compile("".join(parts))


def token_form(token: str, slug: str | None) -> str:
    """What a token of the pattern stands for: the slug named, or any of its kind."""
    if token == SLUG and slug:
        return re.escape(slug)
    return TOKENS[token]


def name(pattern: str, slug: str, day: date) -> str:
    """The name the plan of `slug` takes when it is written on `day`."""
    year, month, of_month = day.isoformat().split("-")
    named = pattern.replace(SLUG, slug).replace("YYYY", year)
    return named.replace("MM", month).replace("DD", of_month)


def newest(names: Iterable[str], pattern: str, slugs: Iterable[str]) -> str | None:
    """Of `names`, the plan of the first of `slugs` that has one, the newest day's of
    several; None when none has."""
    listed = tuple(names)
    for slug in slugs:
        form = regex(pattern, slug)
        matches = [found for found in map(form.fullmatch, listed) if found is not None]
        if matches:
            return max(matches, key=placed).string
    return None


def placed(found: re.Match[str]) -> tuple[str, ...]:
    """A plan's place among a task's plans: its day, then its name."""
    day = found.groupdict()
    parts = [day.get(key) or "" for key in DAY_KEYS]
    return (*parts, found.string)


def chain(slug: str, every: tuple[Record, ...]) -> Slugs:
    """The task `slug`, then the tasks it was resumed from, the nearest first."""
    came_from = {record.task.slug: record.task.resumed_from for record in every}
    found = [slug]
    here = came_from.get(slug)
    while here is not None and here not in found:
        found.append(here)
        here = came_from.get(here)
    return tuple(found)


def day_of(given: str | None, today: date) -> date:
    """The day a plan is written: `given` as YYYY-MM-DD, else today."""
    if given is None:
        return today
    try:
        return date.fromisoformat(given if DAY.fullmatch(given) else "")
    except ValueError as error:
        raise Refusal(
            "date",
            f"--date {given!r} is not a day as YYYY-MM-DD",
            "give the day as 2026-11-25, or leave --date out for today",
        ) from error
