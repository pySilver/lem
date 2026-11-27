"""The backlog items that count as work, from both folders."""

from typing import TYPE_CHECKING

from lem.board.views.backlog.groups import worth_of

if TYPE_CHECKING:
    from lem.board.views.backlog_read import Entry, Shelved


def work_entries(shelved: Shelved) -> tuple[Entry, ...]:
    """The items the owner can still do or has a task for."""
    return tuple(entry for entry in shelved.entries if worth_of(entry) != "no")


def work_count(shelved: Shelved | None) -> int | None:
    """The count on the Backlog key, None with no read."""
    return None if shelved is None else len(work_entries(shelved))
