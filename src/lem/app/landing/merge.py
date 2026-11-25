"""`lem land merge`: the merge of the open pull request, under the workspace's merge lock.

Under the lock the record and the world are read again (a fetch of origin, the worktree's tip,
the forge's pull request): an intent on record is reconciled with what the forge shows before
any new call, and a new call goes, while only an open pull request is visible, on the owner's
word alone. Else the evidence is checked again, the intent is written, the forge's merge is
called with the proposed tip as the head it must have, and its answer is written
(`reconcile.py`). A merge that waits for another task's holds a `MergeWait` in the journal.
"""

import fcntl
import os
from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import changes, merge_step, merge_world, reconcile
from lem.kernel import locks
from lem.kernel.errors import Refusal
from lem.model.landing import merge
from lem.model.landing import reconcile as rules
from lem.records.base import Frozen
from lem.records.journal.landing import MergeWait
from lem.store import places, steps

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.kernel.envelope import Envelope
    from lem.model.landing.merge_asked import Asked
    from lem.records.landing.merge import MergeIntent

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


@contextmanager
def held(context: Context) -> Iterator[None]:
    """Hold the workspace's merge lock; a merge that finds it held notes whose merge it waits
    for, and waits."""
    path = places.locks_folder(context.workspace.state) / LOCK
    slug = context.record.task.slug
    with path.open("a+", encoding="utf-8") as stream:
        if not locks.taken(stream):
            entry = MergeWait(at=context.world.now, behind=holder_of(path))
            context.write(context.record, partial(changes.noted, entry=entry))
            fcntl.flock(stream, fcntl.LOCK_EX)
        stream.truncate(0)
        stream.write(msgspec.json.encode(Holder(task=slug, pid=os.getpid())).decode())
        stream.flush()
        try:
            yield
        finally:
            stream.truncate(0)
            stream.flush()


def explicit(asked: Asked, intent: MergeIntent, found: object) -> bool:
    """Whether a new call goes over the intent on record: only while GitHub shows the pull
    request open with nothing of the call (`found`, the reconcile's refusal), on the owner's
    explicit word for its tip after his check, never the merge agent's, the server's or his
    standing merge."""
    waits = isinstance(found, Refusal) and found.code == "intent"
    return (
        waits
        and asked.by == "owner"
        and not asked.standing
        and asked.via != "server"
        and asked.tip == intent.tip
    )


def locked(context: Context, asked: Asked) -> object:
    """Under the merge lock, on the record and the world read again: reconcile an intent on
    record, else merge on the evidence as it is now."""
    record = context.record
    intent = record.landing.intent if record.landing else None
    if intent is not None:
        trees = merge_world.trees_of(context, context.world.pull)
        dequeued = merge_world.dequeued_of(context)
        found = rules.reconciled(
            record, context.world, intent, trees, dequeued=dequeued
        )
        if not explicit(asked, intent, found):
            return reconcile.written(context, record, found, intent.by)
    decided = merge.decide(
        record, context.world, asked, merge_world.checks_tree(context)
    )
    if isinstance(decided, Refusal):
        raise reconcile.kept(context, record, decided, asked)
    return reconcile.called(context, record, decided)


def act(context: Context, *, asked: Asked) -> object:
    """Take the merge lock, read the record and the world again, and merge on what they say
    now (`main:land.merge_locked`)."""
    with held(context):
        return locked(context.again(), asked)


def run(folder: Path, slug: str, asked: Asked) -> Envelope:
    """`lem land merge SLUG --by owner|merger [--message M] [--via V] [--standing] [--tip T]`."""
    return merge_step.landed(folder, slug, merge.STEP, partial(act, asked=asked))
