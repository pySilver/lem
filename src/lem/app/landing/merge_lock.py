"""The workspace's merge lock, `.lem/state/locks/merge.lock` (`landing.md` G): one merge call
at a time, with the recheck of what it relies on. The file names the task that holds it, so a
merge that finds it held notes whose merge it waits for (`MergeWait`, `main:land.merge_lock`).
"""

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import changes
from lem.kernel import locks
from lem.records.base import Frozen
from lem.records.journal.landing import MergeWait
from lem.store import places, steps

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from lem.app.landing.frame import Context

LOCK = "merge.lock"


class Holder(Frozen, frozen=True, kw_only=True):
    """Who holds the merge lock: the task and its process."""

    task: str
    pid: int


def holder_of(path: Path) -> str | None:
    """The task whose living process holds the merge lock, as its file names it."""
    try:
        holder = msgspec.json.decode(path.read_bytes(), type=Holder)
    except OSError, msgspec.DecodeError:
        return None
    return holder.task if steps.alive(holder.pid) else None


def waits(context: Context, path: Path) -> None:
    """Note in the journal whose merge this one waits for, when another holds the lock."""
    with locks.tried(path) as free:
        if free is not None:
            return
    entry = MergeWait(at=context.world.now, behind=holder_of(path))
    context.write(context.record, lambda record: changes.noted(record, entry))


@contextmanager
def held(context: Context) -> Iterator[None]:
    """Hold the workspace's merge lock, after a note of the merge it waits for, if any."""
    path = places.locks_folder(context.workspace.state) / LOCK
    named = Holder(task=context.record.task.slug, pid=os.getpid())
    waits(context, path)
    with locks.held(path) as stream:
        stream.truncate(0)
        stream.write(msgspec.json.encode(named).decode())
        stream.flush()
        try:
            yield
        finally:
            stream.truncate(0)
            stream.flush()
