"""The workspace's merge lock, `.lem/state/locks/merge.lock` (`landing.md` G): one merge call
at a time, with the recheck of what it relies on. The file names the task that holds it, so a
merge that finds it held notes whose merge it waits for (`MergeWait`, `main:land.merge_lock`).
"""

import fcntl
import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import changes, merge_mutex
from lem.kernel import locks
from lem.records.journal.landing import MergeWait
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from lem.app.landing.frame import Context

LOCK = "merge.lock"


def waits(context: Context, path: Path) -> None:
    """Note in the journal whose merge this one waits for, when another holds the lock."""
    entry = MergeWait(at=context.world.now, behind=merge_mutex.holder_of(path))
    context.write(context.record, lambda record: changes.noted(record, entry))


@contextmanager
def held(context: Context) -> Iterator[None]:
    """Hold the workspace's merge lock, after a note of the merge it waits for, if any."""
    path = places.locks_folder(context.workspace.state) / LOCK
    slug = context.record.task.slug
    named = merge_mutex.Holder(task=slug, pid=os.getpid())
    with merge_mutex.opened(path, slug) as stream:
        if not locks.taken(stream):
            waits(context, path)
            fcntl.flock(stream, fcntl.LOCK_EX)
        stream.truncate(0)
        stream.write(msgspec.json.encode(named).decode())
        stream.flush()
        try:
            yield
        finally:
            stream.truncate(0)
            stream.flush()
