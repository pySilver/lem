"""The line of what the backlog holds (`board_pages.backlog_page` on `main`): `2 items in
docs/backlog · 2 of the reviewer in .lem/state/backlog, 1 undecided · read 16:00`, with how many
items cannot be read when some cannot."""

from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.names import plural
from lem.board.views.backlog import counts, groups

if TYPE_CHECKING:
    from lem.board.views.backlog_read import Shelved
    from lem.board.views.world import World
    from lem.records.record import Record


def summary_of(world: World, records: tuple[Record, ...]) -> str:
    """The line of what the world's backlog holds; empty with no read."""
    shelved = world.backlog
    if shelved is None:
        return ""
    clock = world.clock
    read = stamp(shelved.read, clock.now, clock.zone)
    parts = (holding(shelved, records), broken_said(shelved), f"read {read}")
    return " · ".join(part for part in parts if part)


def holding(shelved: Shelved, records: tuple[Record, ...]) -> str:
    """How many items count as work in each folder, with how many are undecided."""
    found = counts.work_entries(shelved)
    theirs = sum(1 for entry in found if entry.reviewer)
    mine = plural(len(found) - theirs, "item")
    folder = f"{mine} in {shelved.folder}"
    if not theirs:
        return folder
    waiting = groups.undecided(shelved, records)
    return f"{folder} · {theirs} of the reviewer in {shelved.reviewer}, {waiting} undecided"


def broken_said(shelved: Shelved) -> str:
    """How many items cannot be read; empty when every item reads."""
    broken = sum(1 for entry in shelved.entries if entry.bad is not None)
    return f"{broken} cannot be read" if broken else ""
