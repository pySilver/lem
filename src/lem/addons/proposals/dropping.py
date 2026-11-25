"""`lem proposals drop PATH`: the owner's drop of a reviewer's item, in one call under the records'
lock (`project.cmd_proposals_drop` on `main`).

Refused while a task that has not ended started from the item, and for a `worth: no` item, a
refuted proposal that is decided against already; else the drop of each proposal the item names
is kept in its day's record, which the reviewer of a later morning reads as the owner's no, and
then the item's file goes. The board's Drop runs this command.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.addons.proposals import drop_checks, drop_records, item_files
from lem.records.base import Day, Frozen
from lem.store import reviewer_items

if TYPE_CHECKING:
    import datetime as dt

    from lem.store.places import Workspace


class Dropped(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The drop: the item's path, the proposals whose records keep it, and the day."""

    item_path: str = msgspec.field(name="item")
    proposals: tuple[str, ...]
    day: Day


def dropped(where: Workspace, given: str, today: dt.date) -> Dropped:
    """Drop the reviewer's item `given`, a path from the main checkout or whole under it."""
    path = drop_checks.reviewer_path(where.checkout, given)
    target = item_files.file_of(where.state, path)
    with reviewer_items.held(where.state):
        named = drop_checks.droppable(where.state, target, path)
        drop_records.written(drop_records.kept(where.state, named, path, today))
        target.unlink()
    return Dropped(item_path=path, proposals=named, day=today)
