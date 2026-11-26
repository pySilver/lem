"""`lem task ticket`: one step Lem took on a task's ticket, written down after the tracker took
it (`assigned` before, with the login), accepted after the task's end too (`landing.md` E,
"Ticket after the end")."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app import task_reads
from lem.app.tasks import release
from lem.kernel import clock
from lem.model.task import claim, tickets
from lem.records.base import Frozen
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.tickets import TicketAct

# The steps of a task's end, which pass the release stop as the end itself does.
ENDS = frozenset(("unassigned", "commented", "landed", "dropped", "answered"))


class Shown(Frozen, frozen=True, kw_only=True):
    """A task's ticket: its id and repository, the steps written down, the login Lem added,
    and what its end still owes it."""

    slug: str
    ticket: str
    repo: str | None = None
    steps: tuple[str, ...] = ()
    assignee: str | None = None
    owed: tuple[str, ...] = ()


def shown(record: Record, every: tuple[Record, ...]) -> Shown:
    """What `lem task ticket` and the tracker's steps print of a task's ticket."""
    task = record.task
    ticket = tickets.of(task)
    return Shown(
        slug=task.slug,
        ticket=ticket.id,
        repo=ticket.repo,
        steps=tuple(step.act for step in ticket.steps),
        assignee=tickets.assignee(ticket),
        owed=tickets.owed(task, claim.holder(task, every)),
    )


def with_step(
    record: Record, *, act: TicketAct, login: str | None, now: Moment
) -> Record:
    """The record with the step written down on its ticket."""
    stepped = tickets.stepped(tickets.of(record.task), act, login, now)
    return replace(record, task=replace(record.task, ticket=stepped))


def recorded(state: Path, slug: str, act: TicketAct, login: str | None) -> Shown:
    """Write down the step `act` on the ticket of `slug`, and give the ticket as it is now."""
    record = release.checked(state, slug, ends=act in ENDS)
    now = clock.now()
    written = tasks.update(
        state,
        slug,
        lambda one: with_step(one, act=act, login=login, now=now),
        record.revision,
    )
    return shown(written, task_reads.visible(state))


def stepped(folder: Path, slug: str, act: TicketAct, login: str | None) -> Shown:
    """`lem task ticket SLUG STEP [--login L]` from the folder of the call."""
    return recorded(places.workspace(folder).state, slug, act, login)
