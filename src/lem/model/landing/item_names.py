"""The file of the item `file` writes for a defect a review saw outside the change: its name in
the backlog folder, and its text in the item format of rule 6 (`land.names_for` and
`land.item_body` on `main`)."""

import itertools
import re
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from lem.records.base import Frozen

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.model.landing.items import Defect

# The longest file name an item gets from its title, before `.md` (`SLUG_AT` on `main`): a guess
# of 2026-11-16, not a measurement, long enough for a title of a dozen words.
SLUG_AT = 80
# The paragraph of an item filed over the bar for a defect whose open item says `worth: no`:
# the old item stays as it is, and the new one names it (`NOW_OVER` on `main`).
NOW_OVER = "The same defect as `{0}`, now over the bar."


class Written(Frozen, frozen=True, kw_only=True):
    """What an item's text says besides its defect: its worth, the day it was added, where it
    was seen, the review's reason for an item under the bar, and the old `worth: no` item a
    new `worth: later` one names."""

    worth: str
    added: str
    seen: str
    why: str | None = None
    cites: str | None = None


def slug_of(text: str) -> str:
    """A file name from a title, as the item format has it: its words joined by `-`."""
    # Only lowercase text reaches strip, so a strip set with uppercase X gives the same slug.
    slug = re.sub(r"[\W_]+", "-", text.lower()).strip("-")  # pragma: no mutate
    if len(slug) <= SLUG_AT:
        return slug
    return slug[:SLUG_AT].rsplit("-", 1)[0]


def longer_of(defect: Defect) -> str:
    """The slug of the title with a suffix from the defect's `where`: `src/json.py:parse`
    gives `-json-parse`."""
    slug = slug_of(defect.title)
    path, _, symbol = defect.where.partition(":")
    suffix = slug_of(f"{PurePosixPath(path).stem} {symbol}")
    return f"{slug}-{suffix}" if suffix else slug


def names_for(defect: Defect) -> Iterator[str]:
    """The file names an item of this defect may take, in turn: the slug of its title, the
    longer slug, then that with a number, without end."""
    slug, longer = slug_of(defect.title), longer_of(defect)
    yield f"{slug}.md"
    if longer != slug:
        yield f"{longer}.md"
    yield from map(f"{longer}-{{0}}.md".format, itertools.count(2))


def body(defect: Defect, written: Written) -> str:
    """The item's text: `worth`, `where` and the day `added`, the title, the run, the line of
    the old item it now holds over the bar, where it was seen, and for an item under the bar
    the review's reason as its last line."""
    head = f"---\nworth: {written.worth}\nwhere: {defect.where}\nadded: {written.added}\n---\n"
    run = defect.what.strip()
    parts = [f"{head}# {defect.title}", run]
    if written.cites:
        parts.append(NOW_OVER.format(written.cites))
    parts.append(written.seen)
    if written.worth == "no" and written.why:
        parts.append(f"Decided against: {written.why}")
    parts.append("")
    return "\n\n".join(parts)[:-1]
