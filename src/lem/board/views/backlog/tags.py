"""The tags of an item on the Backlog view (`board_pages.backlog_item` on `main`): who holds it
or that it waits for the owner's start or drop, that it cannot be read or that git does not have
this version yet, and how old it is."""

from typing import TYPE_CHECKING

from lem.board.inputs.parts import Chip
from lem.board.views.backlog.days import days_old
from lem.board.views.backlog.groups import refuted

if TYPE_CHECKING:
    from datetime import datetime, tzinfo

    from lem.board.views.backlog_read import Entry
    from lem.records.record import Record

UNDECIDED = Chip(
    label="undecided",
    look="you",
    title="No task builds this item, and you have not dropped it",
)
UNREADABLE = Chip(
    label="cannot be read",
    look="bad",
    title="The file of this item is a link to nothing, a folder, or not readable",
)
NOT_SAVED = "git does not have this version of the item yet"


def is_new(entry: Entry) -> bool:
    """Whether git has no commit of this version of a readable item."""
    return entry.bad is None and (not entry.tracked or entry.changed)


def tags(
    entry: Entry, held: Record | None, now: datetime, zone: tzinfo
) -> tuple[Chip, ...]:
    """The item's tags, in their order on its line."""
    state = state_tag(entry) if entry.bad is None else UNREADABLE
    marks = (first_tag(entry, held), state, age_tag(entry, now, zone))
    return tuple(tag for tag in marks if tag is not None)


def first_tag(entry: Entry, held: Record | None) -> Chip | None:
    """The task that holds the item; else, for a reviewer's item not refuted, that it waits
    for the owner's start or drop."""
    if held is not None:
        return holder_tag(held)
    return UNDECIDED if entry.reviewer and not refuted(entry) else None


def age_tag(entry: Entry, now: datetime, zone: tzinfo) -> Chip | None:
    """How old the item is, from the day of its `added`: `today`, `3 d`."""
    days = days_old(entry.added_on, now, zone)
    if days is None:
        return None
    said = f"{days} d" if days else "today"
    return Chip(label=said, title=f"added {entry.added_on}")


def holder_tag(held: Record) -> Chip:
    """The tag of the task that builds the item."""
    slug = held.task.slug
    return Chip(
        label=f"held by {slug}", look="lead", title=f"The task {slug} builds this item"
    )


def state_tag(entry: Entry) -> Chip | None:
    """The tag of a version git does not have: a new item, or an edited one."""
    if not is_new(entry):
        return None
    said = "edited, not committed" if entry.tracked else "new, not committed"
    return Chip(label=said, look="gate", title=NOT_SAVED)
