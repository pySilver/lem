"""The forge's merge call: the intent written first, the call pinned to the proposed tip, and
its answer written down (`landing.md` C, "In `open`"; E, "Stop or lost reply around the merge
call"; `main:land.merge_locked`).

The intent stays when the call ends with no answer (a lost reply raises `Unanswered`, a fault):
only what the forge shows replaces it, under the merge lock, before any new call.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes, merge_world, reconcile
from lem.app.landing.world import seen
from lem.model.landing.reconcile import landed
from lem.ports import forge_facts
from lem.records.landing import merge as facts

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.app.landing.frame import Context
    from lem.model.landing.merge_call import Merging
    from lem.model.landing.world import PullSeen
    from lem.records.record import Record

type BeforeCall = Callable[[facts.MergeIntent], None]


def merged_pull(context: Context, number: int, done: forge_facts.MergeDone) -> PullSeen:
    """The pull request after the forge merged it, its destination as the forge reports it,
    with the merge's own commits where the report lags behind the merge."""
    pull = seen(context.ports.forge.pull(number))
    if pull.state == "merged":
        return pull
    return replace(
        pull,
        state="merged",
        merge_commit=done.commit,
        merged_head=done.merged_head,
        base_parent=done.base_parent,
    )


def held(
    intent: facts.MergeIntent,
    outcome: forge_facts.MergeDenied | forge_facts.MergeTaken,
    context: Context,
) -> facts.MergeAccepted | facts.Refused:
    """What the forge holds of a call it did not merge: the queue that took it, or GitHub's
    refusal in its words."""
    now = context.world.now
    if isinstance(outcome, forge_facts.MergeTaken):
        return facts.MergeAccepted(tip=intent.tip, at=now, queued=outcome.queued)
    return facts.Refused(
        tip=intent.tip,
        source="github",
        kind=outcome.kind,
        line=outcome.said,
        by=intent.by,
        at=now,
    )


def answered(
    context: Context,
    record: Record,
    intent: facts.MergeIntent,
    said: tuple[int, forge_facts.MergeOutcome],
) -> object:
    """Write what the forge answered the merge call of `intent` (`said`: the pull request's
    number and the answer): the merge, the queue that took it, or GitHub's refusal."""
    number, outcome = said
    if not isinstance(outcome, forge_facts.MergeDone):
        return reconcile.written(
            context, record, held(intent, outcome, context), intent.by
        )
    pull = merged_pull(context, number, outcome)
    proof = (intent.by, intent.via, merge_world.trees_of(context, pull))
    return reconcile.written(
        context, record, landed(record, context.world, pull, proof), intent.by
    )


def called(
    context: Context, record: Record, merging: Merging, before_call: BeforeCall | None
) -> object:
    """Write the intent, call the forge's merge pinned to its tip, and write its answer. A
    call that ends with no answer raises and leaves the intent for the reconcile."""
    intent = merging.intent
    number = record.landing.pull.number if record.landing and record.landing.pull else 0
    written = context.write(
        record, lambda before: changes.landing(before, intent=intent)
    )
    text = forge_facts.MergeText(subject=merging.subject, body=merging.body)
    if before_call is not None:
        before_call(intent)
    outcome = context.ports.forge.merge(number, intent.tip, merging.method, text)
    return answered(context, written, intent, (number, outcome))
