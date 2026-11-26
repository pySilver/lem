"""Who holds an ended task's ticket now, and what its end still owes it, when some records of
the workspace did not read: a damaged record may be the resumed task that holds the ticket, so
the tracker gets no step while the owner restores it (decision 30, amended 2026-11-26)."""

from typing import TYPE_CHECKING, NamedTuple

from lem.model.task import claim, tickets

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task
    from lem.records.tickets import TicketAct


# The paths of the records that did not read.
type Paths = tuple[str, ...]


class Owner(NamedTuple):
    """The task that holds the ticket now, the steps its end owes, and the records that did
    not read, one of which may hold it, when they leave that unknown."""

    held_by: str | None
    owed: tuple[TicketAct, ...]
    unknown: Paths


def owner(task: Task, every: tuple[Record, ...], unread: Paths) -> Owner:
    """The ticket's holder and what it is owed; nothing owed while an unread record could
    hold it."""
    held_by = claim.holder(task, every)
    owed = tickets.owed(task, held_by)
    if owed and unread:
        return Owner(held_by=None, owed=(), unknown=unread)
    return Owner(held_by=held_by, owed=owed, unknown=())
