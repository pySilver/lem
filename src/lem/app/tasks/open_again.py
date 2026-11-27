"""The same `lem task open` again: a retry of the same words under the same slug passes, and
other words, another ticket or another feature under that slug are another request, refused. A
part found again before its feature waits for it goes on to the open's fetch and its join
(`feature.py`).
"""

from typing import TYPE_CHECKING

from lem.app.tasks import feature
from lem.app.tasks.opening import ticket_of
from lem.kernel import errors
from lem.model.task import claim, part_of

if TYPE_CHECKING:
    from lem.app.tasks.opening import Asked
    from lem.records.record import Record
    from lem.records.task import Task
    from lem.records.tickets import Ticket, Tracker


def again(
    every: tuple[Record, ...], asked: Asked, ticket: Ticket | None
) -> Record | None:
    """The task of the same slug when its words and its ticket are the same (a retry), or
    None when there is none; refused when it holds other words, another ticket, or ended."""
    same = (one for one in every if one.task.slug == asked.slug)
    found = next(same, None)
    if found is None:
        return None
    task = found.task
    if task.status in claim.ENDED:
        raise errors.Refusal(
            "task-ended",
            f"the task {task.slug} is {task.status}, and a new task takes a slug of its own",
            "add a word to the slug",
        )
    if task.ask.split() != asked.ask.split():
        raise errors.Refusal(
            "task-exists",
            f"the task {task.slug} holds other words already ({task.ask!r}), and a "
            "task's words are written once",
            "this is another request under the same name: add a word to the slug",
        )
    if ticket is not None and not claim.same(task.ticket, ticket):
        raise errors.Refusal(
            "task-exists",
            f"the task {task.slug} holds another ticket than {ticket.id}",
            f"give the task for {ticket.id} another slug",
        )
    return found


def existing(
    every: tuple[Record, ...], asked: Asked, kind: Tracker | None
) -> Task | None:
    """The task an item already has on the board, or the same open asked for again; refused
    when the same slug names another feature."""
    retry = earlier(every, asked, kind)
    if retry is None:
        return None
    refused = part_of.same_part(retry, asked.part_of)
    if retry.slug == asked.slug and refused is not None:
        raise refused
    return retry


def done(
    every: tuple[Record, ...],
    asked: Asked,
    kind: Tracker | None,
) -> Task | None:
    """The task found again when nothing is left to write for it (`feature.waiting`)."""
    retry = existing(every, asked, kind)
    if retry is None or not feature.waiting(every, retry):
        return None
    return retry


def earlier(
    every: tuple[Record, ...], asked: Asked, kind: Tracker | None
) -> Task | None:
    """The task an item already has on the board, or the same open asked for again."""
    if asked.owner_act is not None and asked.backlog_item is not None:
        holding = claim.item_holder(asked.backlog_item, every)
        if holding is not None:
            return holding
    retry = again(every, asked, ticket_of(asked, kind))
    return None if retry is None else retry.task
