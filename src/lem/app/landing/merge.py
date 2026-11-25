"""`lem land merge`: the merge of the open pull request, under the workspace's merge lock.

Under the lock the record and the world are read again (a fetch of origin, the worktree's tip,
the forge's pull request): an intent on record is reconciled with what the forge shows before
any new call, and a new call goes, while only an open pull request is visible, on the owner's
word alone. Else the evidence is checked again, the intent is written, the forge's merge is
called with the proposed tip as the head it must have, and its answer is written
(`reconcile.py`). A merge that waits for another task's holds a `MergeWait` in the journal.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import (
    merge_called,
    merge_lock,
    merge_step,
    merge_word,
    merge_world,
    reconcile,
    step_release,
)
from lem.kernel.errors import Refusal
from lem.model.landing import merge, merge_asked
from lem.model.landing.reconcile import Found, reconciled

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.kernel.envelope import Envelope
    from lem.records.landing.merge import MergeIntent


def shown(context: Context, intent: MergeIntent) -> Refusal | Found:
    """What the forge shows of the intent on record: the merge, the queue, the queue's end,
    the end of a closed request, or the refusal that keeps the intent."""
    trees = merge_world.trees_of(context, context.world.pull)
    return reconciled(context.record, context.world, intent, trees)


def locked(
    context: Context,
    asked: merge_asked.Asked,
    before_call: merge_called.BeforeCall | None = None,
) -> object:
    """Under the merge lock, on the record and the world read again: reconcile an intent on
    record, else merge on the evidence as it is now."""
    record = context.record
    stale = merge_asked.tip_refusal(record, asked, context.world)
    if stale is not None:
        raise stale
    intent = record.landing.intent if record.landing else None
    if intent is None:
        merge_word.unchecked(asked)
    else:
        found = shown(context, intent)
        if not merge_word.explicit(asked, intent, found):
            return reconcile.written(context, record, found, intent.by)
        record = merge_word.heard(context, record, intent)
    decided = merge.decide(
        record, context.world, asked, merge_world.checks_tree(context)
    )
    if isinstance(decided, Refusal):
        raise reconcile.kept(context, record, decided, asked)
    return merge_called.called(context, record, decided, before_call)


def act(
    context: Context,
    *,
    asked: merge_asked.Asked,
    before_call: merge_called.BeforeCall | None = None,
) -> object:
    """Take the merge lock, read the record and the world again, and merge on what they say
    now (`main:land.merge_locked`)."""
    with merge_lock.held(context):
        refreshed = context.again(ends=step_release.has_intent(context.record))
        return locked(refreshed, asked, before_call)


def run(
    folder: Path,
    slug: str,
    asked: merge_asked.Asked,
    *,
    before_call: merge_called.BeforeCall | None = None,
) -> Envelope:
    """`lem land merge SLUG --by owner|merger [--message M] [--via V] [--standing] [--tip T]
    [--checked MOMENT]`."""
    hooks = merge_step.Hooks(admits=partial(merge_word.admits, asked))
    action = partial(act, asked=asked, before_call=before_call)
    return merge_step.landed(folder, slug, merge.STEP, action, hooks)
