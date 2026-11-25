"""The forge's merge call: the intent written first, the call pinned to the proposed tip, and
its answer written down (`landing.md` C, "In `open`"; E, "Stop or lost reply around the merge
call"; `main:land.merge_locked`).

The intent stays when the call ends with no answer (a lost reply raises `Unanswered`, a fault):
only what the forge shows replaces it, under the merge lock, before any new call.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes, merge_reply, pull_identity, reconcile
from lem.kernel import clock
from lem.ports import forge_facts
from lem.records.landing import merge as facts

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.app.landing.frame import Context
    from lem.model.landing.merge_call import Merging
    from lem.records.record import Record

type BeforeCall = Callable[[facts.MergeIntent], None]


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
        pull_identity.checked(record, context.ports.forge.pull(number))
        return reconcile.written(
            context, record, merge_reply.held(intent, outcome, context), intent.by
        )
    return reconcile.adopted(
        context, record, merge_reply.merged_pull(context, number, outcome)
    )


def called(
    context: Context, record: Record, merging: Merging, before_call: BeforeCall | None
) -> object:
    """Write the intent, call the forge's merge pinned to its tip, and write its answer. A
    call that ends with no answer raises and leaves the intent for the reconcile."""
    intent = replace(merging.intent, at=clock.now())
    number = record.landing.pull.number if record.landing and record.landing.pull else 0
    written = context.write(
        record, lambda before: changes.landing(before, intent=intent)
    )
    text = forge_facts.MergeText(subject=merging.subject, body=merging.body)
    if before_call is not None:
        before_call(intent)
    outcome = context.ports.forge.merge(number, intent.tip, merging.method, text)
    return answered(context, written, intent, (number, outcome))
