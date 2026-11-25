"""The claims of a new task, over every record under the workspace lock (the design's part 3,
"Locks"): one ticket is one task, and one backlog item is one open task.

A ticket stays claimed by a landed task for good, and by a dropped or answered task while it owes
the ticket a step (`project.released`, `holder_refusal` on `main`). A resumed task takes the
ticket of the task it goes on from. A backlog item is claimed by any open task that started from
it. The scan of every record and the publication of the new one are under one lock, so of two
opens at one moment one takes the ticket.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.task import tickets

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task
    from lem.records.tickets import Ticket, Tracker

ENDED = frozenset(("landed", "dropped", "answered"))
RETURNED = frozenset(("dropped", "answered"))


def holder(task: Task, every: tuple[Record, ...]) -> str | None:
    """The task that holds `task`'s ticket now when it is another one: the task a resume went
    on in, with the same ticket."""
    ticket = task.ticket
    if ticket is None:
        return None
    went_on = (other.task for other in every if other.task.resumed_from == task.slug)
    return next((other.slug for other in went_on if same(other.ticket, ticket)), None)


def same(one: Ticket | None, other: Ticket) -> bool:
    """Whether two tickets are the one ticket: the same tracker, id and repository."""
    if one is None:
        return False
    named = (one.tracker, one.id, one.repo)
    return named == (other.tracker, other.id, other.repo)


def released(task: Task, every: tuple[Record, ...]) -> bool:
    """Whether a task gave its ticket back: dropped or answered and owing it nothing, or
    went on in a resumed task that holds it now."""
    if holder(task, every) is not None:
        return True
    return task.status in RETURNED and not tickets.owed(task, None)


def holder_refusal(task: Task, kind: Tracker | None) -> Refusal:
    """Why a new task cannot take the ticket `task` holds, with the way on."""
    slug, ticket = task.slug, task.ticket.id if task.ticket else ""
    if task.status == "landed":
        return Refusal(
            "ticket-landed",
            f"the task {slug} landed the ticket {ticket}, and a ticket that landed stays "
            "with its task",
            "start the new task from the owner's own words (--ask), with no --ticket",
        )
    if task.status in RETURNED:
        step = "drop" if task.status == "dropped" else "answer"
        pay = (
            f"lem issue {step} {slug}"
            if kind == "github"
            else f"the lem-linear skill's step {step} for {slug}, run from a session"
        )
        owes = ", ".join(tickets.owed(task, None))
        return Refusal(
            "ticket-owed",
            f"the task {slug} is {task.status} and still owes the ticket {ticket} {owes}",
            f"pay it with {pay}, then open this task again",
        )
    return Refusal(
        "ticket-held",
        f"the task {slug} already holds the ticket {ticket}",
        f"go on with {slug}, or drop it first",
    )


def ticket_claim(made: Record, every: tuple[Record, ...], kind: Tracker | None) -> None:
    """Refuse `made` when another task holds its ticket; the task it goes on from does not."""
    ticket = made.task.ticket
    if ticket is None:
        return
    holders = (
        other.task
        for other in every
        if same(other.task.ticket, ticket) and other.task.slug != made.task.resumed_from
    )
    held = next((task for task in holders if not released(task, every)), None)
    if held is not None:
        raise holder_refusal(held, kind)


def item_claim(made: Record, every: tuple[Record, ...]) -> None:
    """Refuse `made` when an open task started from its backlog item already."""
    path = made.task.backlog_item
    if path is None:
        return
    holding = next(
        (
            other.task.slug
            for other in every
            if other.task.backlog_item == path and other.task.status not in ENDED
        ),
        None,
    )
    if holding is not None:
        raise Refusal(
            "item-held",
            f"the open task {holding} started from the backlog item {path} already",
            f"go on with {holding}, or drop it first",
        )


def claimed(made: Record, every: tuple[Record, ...], kind: Tracker | None) -> Record:
    """The new record, once every record is read under the workspace lock: refused when its
    ticket or its item is held."""
    ticket_claim(made, every, kind)
    item_claim(made, every)
    return made
