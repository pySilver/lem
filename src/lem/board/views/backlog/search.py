"""The backlog's rows of the search over every card (the items' part of `board_model.search_rows`
on `main`): the reviewer's items, the undecided ones first, then the other items by their worth,
the reviewer's refuted ones among those of Decided against. Each opens the Backlog view at its
item."""

from typing import TYPE_CHECKING
from urllib.parse import quote

from lem.board.inputs.search import Found
from lem.board.views.backlog import groups

if TYPE_CHECKING:
    from lem.board.inputs.text import Href, Look
    from lem.board.views.backlog_read import Entry, Shelved
    from lem.records.record import Record

CHIP = "Backlog · {said}"


def search_rows(
    shelved: Shelved | None, records: tuple[Record, ...], base: Href
) -> tuple[Found, ...]:
    """The item rows of the search, in its order; none with no read."""
    if shelved is None:
        return ()
    mine = tuple(
        row(entry, base, *reviewer_said(held))
        for entry, held in groups.reviewer_entries(shelved, records)
    )
    theirs = tuple(
        row(entry, base, f"worth: {group.key}", group.look)
        for group in groups.BY_WORTH
        for entry in groups.worth_entries(shelved, group.key)
    )
    return (*mine, *theirs)


def reviewer_said(held: Record | None) -> tuple[str, Look]:
    """The chip's words and look of a reviewer's item: held by its task, or undecided."""
    if held is None:
        return "undecided", "you"
    slug = held.task.slug
    return f"held by {slug}", "lead"


def row(entry: Entry, base: Href, said: str, look: Look) -> Found:
    """The row of one item."""
    key = entry.key
    return Found(
        kind="item",
        key=key,
        title=" ".join(entry.title.split()),
        chip=CHIP.format(said=said),
        look=look,
        href=f"{base}/backlog#item-{quote(key, safe='')}",
    )
