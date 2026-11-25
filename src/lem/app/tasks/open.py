"""`lem task open`: a task's record and its folder, under the workspace's claim lock.

The task opens `shaping`, with the owner's words as he gave them and the branch a tracker named,
if one did. A ticket, a backlog item, a night, a queue behind another task and the claim of each
are the step `task`'s.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.kernel import clock, release
from lem.records.base import Frozen
from lem.records.journal.task import StateNoted
from lem.records.record import Record
from lem.records.task import Task
from lem.store import places, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment

SHAPING = "shaping"


class Opened(Frozen, frozen=True, kw_only=True):
    """The task opened: its slug, its folder and its status."""

    slug: str
    folder: str
    status: str


def claimed(made: Record, every: tuple[Record, ...]) -> Record:
    """The new record, once every record is read under the claim lock; the claims of a
    ticket and an item are the step `task`'s."""
    return made


def fresh(slug: str, words: tuple[str, str | None], now: Moment) -> Record:
    """The first record of a task: `words` are the ask and the branch."""
    ask, branch = words
    task = Task(
        slug=slug, ask=ask, opened=now, status=SHAPING, since=now, branch=branch
    )
    entry = StateNoted(at=now, status=SHAPING, line="the task is open")
    return Record(release=release.running(), task=task, journal=(entry,))


def opened(folder: Path, slug: str, *, ask: str, branch: str | None) -> Opened:
    """Open the task `slug` with the owner's words `ask`."""
    state = places.state_of(places.workspace(folder).checkout)
    made = fresh(slug, (ask, branch), clock.now())
    workspace.claimed(state, partial(claimed, made))
    where = str(places.task_folder(state, slug))
    return Opened(slug=slug, folder=where, status=SHAPING)
