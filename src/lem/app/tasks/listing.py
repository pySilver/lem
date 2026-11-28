"""`lem task list` and `lem task show`: each task as its record says now (`project.read_tasks`
on `main`), with what its ticket still owes and who holds it.

A task's mode is the one its record keeps (a night task runs alone from its opening); whether the
owner is away now is the owner's status, which `lem waiting` joins.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app import task_reads
from lem.app.tasks import first_line, shown_answer
from lem.model.task import claim, feature_parts, ticket_owner, tickets
from lem.records import task, work
from lem.records.base import Day, Frozen, Moment
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked, ReleaseHold
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.holds import Hold
    from lem.records.record import Record


class TicketRow(Frozen, frozen=True, kw_only=True):
    """A task's ticket: its id and repository, the steps written down, the login Lem added,
    what its end still owes, the task that holds it now when it is another one, and the
    records that did not read when one of them may hold it, which leave nothing owed."""

    id: str
    repo: str | None = None
    steps: tuple[str, ...] = ()
    assignee: str | None = None
    owed: tuple[str, ...] = ()
    held_by: str | None = None
    holder_unknown: tuple[str, ...] = ()


class Row(Frozen, frozen=True, kw_only=True):
    """One task, as `lem task list` and `lem task show` print it."""

    slug: str
    ask: str
    status: str
    since: Moment
    hold: str | None = None
    hold_line: str | None = None
    type: str | None = None
    track: str | None = None
    branch: str | None = None
    after: tuple[str, ...] = ()
    order: str | None = None
    part_of: str | None = None
    parts: tuple[str, ...] = ()
    plan_only: bool = False
    night: Day | None = None
    mode: str
    ticket: TicketRow | None = None
    backlog_item: str | None = None
    resumed_from: str | None = None
    first_line: str | None = None
    owner_careful: Moment | None = None
    shape: task.Shape | None = None
    lead: str | None = None
    plan: work.Plan | None = None
    investigation: work.Investigation | None = None
    talk: work.Talk | None = None
    board_answer: shown_answer.BoardAnswer | None = None


def hold_line(hold: Hold | None) -> str | None:
    """What a hold says, in one line."""
    if isinstance(hold, OwnerHold):
        return hold.line
    if isinstance(hold, BreakerHold):
        return f"breaker {hold.number} waits for the owner"
    if isinstance(hold, Blocked):
        return hold.why
    if isinstance(hold, (Parked, ReleaseHold)):
        return hold.words if isinstance(hold, Parked) else hold.say
    return None


def ticket_row(record: Record, read: task_reads.Shown) -> TicketRow | None:
    """The task's ticket as a row, or None."""
    task = record.task
    if task.ticket is None:
        return None
    found = ticket_owner.owner(task, read.records, read.unread)
    return TicketRow(
        id=task.ticket.id,
        repo=task.ticket.repo,
        steps=tuple(step.act for step in task.ticket.steps),
        assignee=tickets.assignee(task.ticket),
        owed=found.owed,
        held_by=found.held_by,
        holder_unknown=found.unknown,
    )


def row(record: Record, read: task_reads.Shown) -> Row:
    """One task's row."""
    task, shape = record.task, record.task.shape
    hold = task.hold
    return Row(
        slug=task.slug,
        ask=task.ask,
        status=task.status,
        since=task.since,
        hold=None if hold is None else type(hold).__name__,
        hold_line=hold_line(hold),
        type=None if shape is None else shape.type,
        track=None if shape is None else shape.track,
        branch=task.branch,
        after=task.after,
        order=task.order,
        part_of=task.part_of,
        parts=feature_parts.named_parts(task, (one.task for one in read.records)),
        plan_only=task.plan_only,
        night=task.night,
        mode=task.mode,
        ticket=ticket_row(record, read),
        backlog_item=task.backlog_item,
        resumed_from=task.resumed_from,
        owner_careful=task.owner_careful,
    )


def listed(folder: Path, *, ended: bool) -> tuple[Row, ...]:
    """Every task of the workspace, the ended ones only with `ended`."""
    state = places.workspace(folder).state
    read = task_reads.surveyed(state)
    return tuple(
        row(record, read)
        for record in read.records
        if ended or record.task.status not in claim.ENDED
    )


def shown(folder: Path, slug: str) -> Row:
    """One task; a read, which writes nothing, the release stop's hold neither."""
    where = places.workspace(folder)
    record = tasks.read(where.state, slug)
    line = first_line.said(where, record, named=True)
    return replace(
        row(record, task_reads.surveyed(where.state)),
        first_line=line,
        shape=record.task.shape,
        lead=record.task.lead,
        plan=record.task.plan,
        investigation=record.task.investigation,
        talk=record.task.talk,
        board_answer=shown_answer.pending(record),
    )
