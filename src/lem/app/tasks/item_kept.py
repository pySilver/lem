"""`lem task keep-item`: the task's backlog item stays in the backlog, with the reason, written
on the task's record under its lock (`model/task/item_kept.py`)."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.kernel import clock
from lem.model.task import item_kept
from lem.records.base import Frozen
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path


class Kept(Frozen, frozen=True, kw_only=True):
    """The task, and the item that stays."""

    slug: str
    stays: str


def kept(folder: Path, slug: str, why: str) -> Kept:
    """Leave the item of `slug` to the backlog, for the reason `why`."""
    state = places.workspace(folder).state
    record = release.checked(state, slug)
    stays = record.task.backlog_item or ""
    change = partial(item_kept.kept, why=why, now=clock.now())
    tasks.update(state, slug, change, record.revision)
    return Kept(slug=slug, stays=stays)
