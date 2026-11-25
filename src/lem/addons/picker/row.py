"""One row of the picker, as agterm's picker shows it and `lem picker --list` prints it."""

from typing import TYPE_CHECKING

from lem.addons.picker import words
from lem.ports.terminal import PickRow

if TYPE_CHECKING:
    import datetime as dt

    from lem.records.record import Record

# The id of the row for the board of all tasks: no slug holds a colon.
ALL = ":all"


def all_row(count: int) -> PickRow:
    """The last row, the board of every task."""
    tasks = "1 task" if count == 1 else f"{count} tasks"
    every = f"the board of every task · {tasks}"
    return PickRow(row_id=ALL, label="All tasks", subtitle=every)


def pick_row(record: Record, said: str | None, now: dt.datetime) -> PickRow:
    """The row of one task, its state in the words of its wait when it has them."""
    task = record.task
    track = words.TRACKS[task.shape.track] if task.shape else ""
    parts = (
        said or words.state_words(task),
        track,
        words.age(task.since, now),
        words.pull_words(record),
    )
    subtitle = " · ".join(part for part in parts if part)
    return PickRow(row_id=task.slug, label=words.label(task), subtitle=subtitle)
