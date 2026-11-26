"""The records a command can show, with each omitted file on standard error."""

import sys
from typing import TYPE_CHECKING

from lem.store import survey

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def warned(lines: tuple[str, ...]) -> None:
    """Tell the owner which records the command omitted."""
    for line in lines:
        sys.stderr.write(f"{line}\n")


def visible(state: Path) -> tuple[Record, ...]:
    """The workspace records that read, with a line for each one left out."""
    records, unread = survey.records(state)
    warned(survey.warnings(state, unread))
    return records
