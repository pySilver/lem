"""The forge's merge reply as the landing can record it."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing.world import seen
from lem.model.landing.reconcile_queue import accepted
from lem.ports import forge_facts
from lem.records.landing import merge as facts

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.world import PullSeen


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
        return accepted(intent, outcome.queued)
    return facts.Refused(
        tip=intent.tip,
        source="github",
        kind=outcome.kind,
        line=outcome.said,
        by=intent.by,
        at=now,
    )
