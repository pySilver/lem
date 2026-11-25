"""The chips of the backlog's filter (`board_pages.backlog_page` on `main`): every item, each
worth some item gives itself, and each fact, with how many items each keeps and the address that
turns it on, or off on a second press.

The view keeps every item; the page's controller hides those the filter leaves out.
"""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.inputs.backlog import Filter
from lem.board.views.backlog import groups
from lem.board.views.backlog.tags import is_new
from lem.board.views.backlog.wanted import ONLY, WORTH

if TYPE_CHECKING:
    from lem.board.inputs.text import Href, Look
    from lem.board.views.backlog.wanted import Wanted
    from lem.board.views.backlog_read import Entry

type Entries = tuple[Entry, ...]


class Spec(NamedTuple):
    """A chip: its key and the value it sets, its words and look, and what it keeps."""

    key: str
    shown: str
    label: str
    look: Look
    keeps: str


FACTS = (
    Spec(
        ONLY,
        "stale",
        "Where no longer resolves",
        "bad",
        "where the place the item names is not there any more",
    ),
    Spec(
        ONLY, "new", "Not committed", "gate", "added or edited, and not committed yet"
    ),
)


def chips(entries: Entries, want: Wanted, base: Href) -> tuple[Filter, ...]:
    """The chips of the filter: each worth some item gives itself, then each fact."""
    worths = (
        Spec(WORTH, group.key, group.name, group.look, f"whose worth is {group.key}")
        for group in groups.BY_WORTH
    )
    specs = (*worths, *FACTS)
    counted = ((spec, count_of(spec, entries)) for spec in specs)
    return tuple(
        chip(spec, count, want, base)
        for spec, count in counted
        if count or spec.key == ONLY
    )


def count_of(spec: Spec, entries: Entries) -> int:
    """How many items the chip keeps."""
    if spec.key == WORTH:
        return sum(1 for one in entries if groups.worth_of(one) == spec.shown)
    if spec.shown == "new":
        return sum(1 for one in entries if is_new(one))
    return sum(1 for one in entries if one.where and one.where_problem)


def chip(spec: Spec, count: int, want: Wanted, base: Href) -> Filter:
    """A chip of the filter, on when the address asks for its value."""
    return Filter(
        key=spec.key,
        shown=spec.shown,
        label=spec.label,
        look=spec.look,
        count=count,
        on=want.value_of(spec.key) == spec.shown,
        href=want.pressed(spec.key, spec.shown).address(base),
        title=f"Only the items {spec.keeps}",
    )


def every(entries: Entries, want: Wanted, base: Href) -> Filter:
    """The chip of every item, which turns the filter off."""
    return Filter(
        key="",
        shown="",
        label="All",
        count=len(entries),
        on=not (want.words or want.worth or want.only),
        href=f"{base}/backlog",
        title="Every item: the filter off",
    )
