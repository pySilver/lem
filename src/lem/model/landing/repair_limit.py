"""The ordinary landing that waits after the stage's two repair builders."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing.world import Due
from lem.model.task import red_base
from lem.records.holds import Blocked
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Task

WHY = "two builders could not repair the checks"


def waiting(task: Task) -> Blocked | None:
    """The repair block until the owner gives the word to go on."""
    hold = task.hold
    return hold if isinstance(hold, Blocked) and hold.why == WHY else None


def allowed(record: Record) -> bool:
    """Only a failed run in an ordinary landing takes this hold."""
    landing = record.landing
    if landing is None or landing.standing is not None:
        return False
    return (
        record.task.status == "landing"
        and record.task.hold is None
        and landing.checked is not None
        and landing.checked.outcome in {"red", "refused"}
    )


def blocked(record: Record, now: Moment) -> Record:
    """Keep the stage's block for the board, with its way on."""
    task = record.task
    if waiting(task) is not None:
        return record
    if not allowed(record):
        raise Refusal(
            "repair-limit",
            "only a failed check in a landing with no hold or standing approval can wait",
            "a standing approval takes the ladder; otherwise follow the checks' result",
        )
    fix = f'on the owner\'s word, lem task move {task.slug} ready --line "go on" clears the hold'
    hold = Blocked(why=WHY, fix=fix, since=now)
    entry = StateNoted(at=now, status="ready", hold="blocked", line=WHY)
    return replace(
        record,
        task=replace(task, status="ready", hold=hold, since=now),
        journal=(*record.journal, entry),
    )


def due(task: Task) -> Due | None:
    """The check repairs that hold the landing for a task or for the owner."""
    limit = waiting(task)
    if limit is not None:
        return Due(step="wait", why=f"{limit.why}: {limit.fix}")
    repair = red_base.dependency(task)
    if repair is None:
        return None
    way_on = red_base.way_on(task.slug, repair)
    return Due(step="wait", why=f"the base is red: {way_on}")
