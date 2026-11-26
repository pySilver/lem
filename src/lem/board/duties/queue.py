"""A duty of the board server: the turn of a task queued after others, once each of them landed
or was answered (`open … queue` and `wake … queue` of `serve.duties` on `main`).

The queued task gets one wake for its wait: its live session (the one its ask was typed in,
which the owner may keep selected, so that its close never comes) gets the line, and with none
alive a session opens. A wait begins when the task became queued (`Task.since`), so a task
queued again behind another task waits anew. Nothing happens while the terminal cannot say
which sessions live, and a queued task behind a dropped one waits for the owner's word. A
record that does not read holds only the turn of a task queued after it; the workspace page
names it (decision 30).
"""

from typing import TYPE_CHECKING

from lem.app.owner import releases
from lem.board.duties import wakes
from lem.model.task.behind import STARTED
from lem.store import survey

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.board.duties.context import Duty
    from lem.records.record import Record


def tick(duty: Duty) -> None:
    """Give its turn to each queued task whose tasks before it ended."""
    records = releases.with_stops(survey.records(duty.state).readable)
    statuses = {record.task.slug: record.task.status for record in records}
    owed = [record for record in records if turn(record, statuses)]
    if not owed or not wakes.known(duty):
        return
    for record in owed:
        task = record.task
        if not wakes.since(duty, task.slug, task.since):
            wakes.woken(duty, task.slug, "queue")


def turn(record: Record, statuses: Mapping[str, str]) -> bool:
    """Whether the queued task's turn came: it has no hold, and each task it is queued after
    landed or was answered by a record that reads."""
    task = record.task
    if task.status != "queued" or task.hold is not None or not task.after:
        return False
    return all(statuses.get(after) in STARTED for after in task.after)
