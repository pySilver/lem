"""One row of the picker, as agterm's picker shows it and `lem picker --list` prints it."""

from typing import TYPE_CHECKING

import msgspec

from lem.addons.picker import words
from lem.records.base import Frozen

if TYPE_CHECKING:
    import datetime as dt

    from lem.records.record import Record

# The id of the row for the board of all tasks: no slug holds a colon.
ALL = ":all"


class PickRow(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """One row: the task's slug, its ask, and its state, track, age and pull request."""

    row_id: str = msgspec.field(name="id")
    label: str
    subtitle: str


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


def lines_of(found: tuple[PickRow, ...]) -> dict[str, str]:
    """Each row as one line of agterm's picker, its label and its state, with the id it
    stands for; a line two tasks share names its task."""
    lines: dict[str, str] = {}
    for one in found:
        line = f"{one.label} · {one.subtitle}"
        if line in lines:
            line = f"{line} ({one.row_id})"
        lines[line] = one.row_id
    return lines
