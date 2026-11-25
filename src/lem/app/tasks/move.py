"""`lem task move`: a task to a status, by the table of statuses (the design's part 3).

The record is read through the release stop; the table refuses a move of an ended task, a
lead's move over a task with its landing, a move over a park or a seat's block, and a move the
table does not have. A drop goes through `app/tasks/drop.py`, under the landing's step lock.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import drop, release
from lem.kernel import clock
from lem.model.task import ending, holds, table
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Status


def change(
    record: Record, *, status: Status, line: str, start_over: str | None, now: Moment
) -> Record:
    """The move as one change of the record: the landing started over first, when asked."""
    if start_over is not None:
        record = ending.started_over(record, start_over)
        line = ending.start_over_line(start_over)
    return holds.moved(record, status=status, line=line, now=now)


def checked(where: places.Workspace, record: Record, status: Status) -> None:
    """Refuse an `answered` with no report to show."""
    if status != "answered":
        return
    report = places.task_folder(where.state, record.task.slug) / "investigation.md"
    refused = ending.answer_refusal(record.task, report=report.is_file())
    if refused is not None:
        raise refused


def moved(
    folder: Path,
    slug: str,
    status: Status,
    lines: tuple[str, ...],
    start_over: str | None = None,
) -> table.Moved:
    """Move the task `slug` to `status`, with the stage's lines."""
    where = places.workspace(folder)
    line = "; ".join(lines) or status
    if status == "dropped":
        return drop.dropped(where, slug, line)
    record = release.checked(where.state, slug)
    refused = table.refusal(record.task, status, start_over) or table.gate(
        record, status, tasks.every(where.state)
    )
    if refused is not None:
        raise refused
    checked(where, record, status)
    write = partial(
        change, status=status, line=line, start_over=start_over, now=clock.now()
    )
    tasks.update(where.state, slug, write, record.revision)
    return table.Moved(slug=slug, was=record.task.status, status=status)
