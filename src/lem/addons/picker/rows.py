"""The picker's rows, in the order a developer reads them (`picker.rows` on `main`): first what
waits for the owner, in the order of the one list of what waits; then the tasks that go on, by
who works on them now, the newest first in each, a parked one last; then the tasks that ended
last, as many as the board's Done column draws; and last a row for the board of all tasks."""

from typing import TYPE_CHECKING

from lem.addons.picker.row import PickRow, all_row, pick_row
from lem.model.owner.waiting import ENDED
from lem.records.holds import BreakerHold, Parked

if TYPE_CHECKING:
    import datetime as dt

    from lem.model.owner.looks import Row, Rows
    from lem.records.record import Record

# The ended tasks the board's Done column draws (`board_model.DONE_SHOWN` on `main`).
DONE_SHOWN = 20
# The order of the tasks that go on: an agent or the checks work on the first, Lem acts on the
# rest.
ACTIVE = ("building", "shaping", "landing", "ready", "planned", "open", "queued")

type Records = dict[str, Record]
# The tasks that wait for the owner, each with the words of its first wait.
type Waited = dict[str, tuple[Record, str | None]]


def rows_of(records: Records, waits: Rows, now: dt.datetime) -> tuple[PickRow, ...]:
    """Every row of the picker; none for a workspace with no task."""
    if not records:
        return ()
    said = waited(records, waits)
    rest = ((record, None) for record in later(records, said))
    ordered = (*said.values(), *rest)
    picked = tuple(pick_row(*pair, now) for pair in ordered)
    return (*picked, all_row(len(records)))


def waited(records: Records, waits: Rows) -> Waited:
    """The tasks that wait for the owner, in the list's order, each once with the words of
    its first wait."""
    said: Waited = {}
    for row in waits:
        record = records.get(row.task)
        if record is not None and row.task not in said:
            said[row.task] = (record, wait_words(row, record))
    return said


def wait_words(row: Row, record: Record) -> str | None:
    """The words of a wait that say more than the task's state: a breaker's, the criteria's,
    and a queue after a dropped task."""
    hold = record.task.hold
    if row.kind == "breaker" and isinstance(hold, BreakerHold):
        return f"Stopped: breaker {hold.number} waits for you"
    if row.kind == "criteria":
        return "Waits for you: the acceptance criteria"
    if row.kind == "after_dropped":
        return f"Waits for you: {row.after} was dropped"
    return None


def later(records: Records, shown: Waited) -> list[Record]:
    """The tasks not `shown` yet: those that go on, by who works on them, the newest first, a
    parked one last; then the ended ones, the newest first, as many as Done draws."""
    left = (record for record in records.values() if record.task.slug not in shown)
    newest = sorted(left, key=since_of, reverse=True)
    going = [record for record in newest if record.task.status not in ENDED]
    ended = [record for record in newest if record.task.status in ENDED]
    return [*sorted(going, key=place_of), *ended[:DONE_SHOWN]]


def since_of(record: Record) -> dt.datetime:
    """When the task's state began."""
    return record.task.since


def place_of(record: Record) -> int:
    """A task's place among the tasks that go on."""
    task = record.task
    if isinstance(task.hold, Parked) or task.status not in ACTIVE:
        return len(ACTIVE)
    return ACTIVE.index(task.status)
