"""Parts of a task's large card (`board_model.who_acts`, `investigation_sub` and
`board_task.now_foot` on `main`): who acts, what its investigation found, the owner's two
other words to a held or parked task, and the card's foot."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs import clock
from lem.board.inputs.task.now import Foot
from lem.board.views.panel import ways
from lem.board.views.panel.common import closed
from lem.records.journal.task import StateNoted, Summary

if TYPE_CHECKING:
    from datetime import datetime

    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.records.record import Record
    from lem.records.work import Investigation

# What an investigation found, as the large card says it (`CALLS[...]["now"]` on `main`).
FOUND = MappingProxyType(
    {
        "small": (
            "A plain cause, which one rule fixes: the task goes on by the fast track"
        ),
        "full": "A plain cause, and the standard track: the interview starts from it",
        "not-a-bug": "No bug: the code does what it should",
        "not-reproduced": "Not reproduced: Lem asks you for one more fact",
        "answer": "The answer",
    }
)
REPORT = "investigation.md"
SHAPING = frozenset(("queued", "shaping"))


def opening(record: Record) -> str | None:
    """The read's first line, through the first move into the build."""
    task = record.task
    if task.shape is None:
        return None
    moved = tuple(
        entry.status
        for entry in record.journal
        if isinstance(entry, StateNoted) and entry.status not in SHAPING
    )
    if task.status in SHAPING and not moved:
        return task.shape.first_line
    if task.status == "building" and moved == ("building",):
        return task.shape.first_line
    return None


def who_acts(standing: Standing, *, parked: bool) -> str:
    """The card's eyebrow: who acts now."""
    if standing.who == "You":
        return "You act"
    if parked:
        return "Nobody acts"
    return "Closed" if standing.who == "Nobody" else f"{standing.who} acts"


def found(investigation: Investigation | None) -> str | None:
    """What the investigation found, where, and whether it reproduced the bug."""
    if investigation is None or investigation.call is None:
        return None
    parts = [investigation.where or ""]
    if investigation.kind == "fix" and investigation.reproduced is not None:
        parts.append("reproduced" if investigation.reproduced else "not reproduced")
    where = " · ".join(part for part in parts if part)
    call, line = FOUND[investigation.call], investigation.line or ""
    said = f"**{call}:** {line}".rstrip()
    return f"{said} · {where}" if where else said


def foot(world: World, seen: Seen, standing: Standing) -> Foot:
    """When the task last moved, its time in its state or when it ended, and the jump."""
    now, since = world.clock.now, standing.since
    updated = clock.gone(moved_at(seen.record), now)
    if closed(seen.record.task):
        timer = clock.fixed(since, now, world.clock.zone)
        return Foot(updated=updated, timer=timer, note=f"after {open_for(seen, since)}")
    jump = ways.jump_of(world, seen)
    timer = clock.since(since, now)
    return Foot(updated=updated, timer=timer, note="in this state", jump=jump)


def open_for(seen: Seen, end: datetime) -> str:
    """How long the task was open until `end`."""
    length = end - seen.record.task.opened
    return clock.length(length.total_seconds())


def moved_at(record: Record) -> datetime:
    """When the task last moved: its newest state's moment, or the summary's last."""
    for entry in reversed(record.journal):
        if isinstance(entry, StateNoted):
            return entry.at
        if isinstance(entry, Summary):
            return entry.last
    return record.task.since
