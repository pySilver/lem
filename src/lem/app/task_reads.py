"""The records a command can show, with each omitted file on standard error."""

import sys
from typing import TYPE_CHECKING, NamedTuple

from lem.store import survey, task_file

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


class Shown(NamedTuple):
    """The records that read, and the path of each record that does not."""

    records: tuple[Record, ...]
    unread: tuple[str, ...]


def warned(lines: tuple[str, ...]) -> None:
    """Tell the owner which records the command omitted."""
    for line in lines:
        sys.stderr.write(f"{line}\n")


def surveyed(state: Path) -> Shown:
    """The workspace records that read and the paths of those that do not, with a line for
    each one left out."""
    records, unread = survey.records(state)
    warned(survey.warnings(state, unread))
    paths = (state / "tasks" / slug / task_file.RECORD for slug in unread)
    return Shown(records, tuple(map(str, paths)))


def visible(state: Path) -> tuple[Record, ...]:
    """The workspace records that read, with a line for each one left out."""
    return surveyed(state).records
