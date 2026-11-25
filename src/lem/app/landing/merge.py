"""`lem land merge`: the merge of the open pull request, under the workspace's merge lock.

Under the lock the record is read again; an intent on record is reconciled with what the forge
shows before any new call. Else the intent is written, then the forge's merge is called with
the proposed tip as the head it must have, and its answer is written (`reconcile.py`).
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import frame, reconcile, step
from lem.kernel import locks
from lem.kernel.errors import Refusal
from lem.model.landing import merge
from lem.model.landing.reconcile import reconciled
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.model.landing.world import Merger
    from lem.records.record import Record

LOCK = "merge.lock"
# Where the merge was asked for, the subject of the one commit, and the tip the caller saw.
type Call = tuple[merge.Via, str | None, str | None]


def locked(
    context: frame.Context, record: Record, by: Merger, call: Call
) -> reconcile.Found:
    """Under the merge lock: reconcile an intent on record, else merge."""
    via, subject, tip = call
    intent = record.landing.intent if record.landing else None
    if intent is not None:
        return reconcile.written(
            context, record, reconciled(record, context.world, intent)
        )
    decided = merge.decide(record, context.world, by, (via, tip))
    if isinstance(decided, Refusal):
        raise decided
    return reconcile.called(context, record, decided, subject)


def act(context: frame.Context, *, by: Merger, call: Call) -> reconcile.Found:
    """Take the merge lock, read the record again, and merge."""
    state = context.workspace.state
    with locks.held(places.locks_folder(state) / LOCK):
        record = tasks.read(state, context.record.task.slug)
        return locked(context, record, by, call)


def run(folder: Path, slug: str, by: Merger, call: Call) -> Envelope:
    """`lem land merge SLUG --by owner|merger [--message M] [--via V] [--tip TIP]`."""
    return step.landed(folder, slug, "merge", partial(act, by=by, call=call))
