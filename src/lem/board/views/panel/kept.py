"""What the summary of a task's journal keeps, as its card lists it (`board_task.summary_card`
on `main`): its state with its end, its opening, its pull request with green or not green, its
type, who worked on it, its careful call, its branch, and its last line, ask and card."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import repository
from lem.board.views.panel.common import careful_of, pull_of, stamp
from lem.board.views.panel.leads import lead_of

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.records.record import Record

LAST = "its last line, its ask and its card"


def kept(world: World, seen: Seen, standing: Standing) -> tuple[str, ...]:
    """Each fact the summary keeps, in words."""
    record = seen.record
    ended = stamp(world, standing.since)
    opened = stamp(world, record.task.opened)
    label = standing.label.lower()
    found = (
        f"{label} {ended}",
        f"opened {opened}",
        *pulled(record),
        *worked(record),
        LAST,
    )
    return tuple(found)


def pulled(record: Record) -> tuple[str, ...]:
    """Its pull request, and green or not green."""
    pull = pull_of(record)
    if pull is None:
        return ()
    named = repository(pull) or ""
    said = (f"pull request {named}#{pull.number}",)
    proposed = record.landing.proposed if record.landing else None
    if proposed is None:
        return said
    return (*said, "green" if proposed.green else "not green")


def worked(record: Record) -> tuple[str, ...]:
    """Its type, who worked on it, its careful call and its branch."""
    task = record.task
    lead, careful = lead_of(record), careful_of(record)
    found = []
    shape = task.shape
    if shape is not None:
        found.append(f"type {shape.type}")
    if lead is not None:
        found.append(f"who worked on it: {lead.tag}")
    if careful is not None:
        found.append("careful: yes" if careful.careful else "careful: no")
    if task.branch:
        found.append(f"branch {task.branch}")
    return tuple(found)
