"""What a merge call left, written down: the forge's merge, its queue, or its refusal in its own
words; and an intent on record replaced by what the forge shows after a stop (`landing.md` C,
"In `open`")."""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes, frame
from lem.app.landing.world import seen
from lem.kernel.errors import Refusal
from lem.model.landing.reconcile import landed
from lem.ports.forge_facts import MergeDenied, MergeTaken, MergeText
from lem.records.journal.merge import MergeNoted
from lem.records.landing.merge import MergeAccepted, Merged, MergeIntent, Refused

if TYPE_CHECKING:
    from lem.ports.forge_facts import MergeOutcome
    from lem.records.record import Record

type Found = Merged | MergeAccepted


def taken(record: Record, *, found: Found) -> Record:
    """The record with the merge or the queue that took it, and the intent cleared."""
    if isinstance(found, MergeAccepted):
        return changes.landing(record, accepted=found, intent=None)
    changed = changes.landing(record, merged=found, intent=None, phase="merged")
    return changes.noted(changed, MergeNoted(at=found.at, merged=found))


def written(context: frame.Context, record: Record, found: Found | Refusal) -> Found:
    """Write what the forge shows, or raise why it is not written."""
    if isinstance(found, Refusal):
        raise found
    context.write(record, partial(taken, found=found))
    return found


def denied(
    context: frame.Context, record: Record, intent: MergeIntent, said: MergeDenied
) -> Refusal:
    """Write the forge's refusal, in its words, and give the step's."""
    refused = Refused(
        tip=intent.tip,
        source="github",
        kind=said.kind,
        line=said.said,
        by=intent.by,
        at=context.world.now,
    )
    change = partial(changes.landing, refused=refused, intent=None)
    context.write(record, change)
    return Refusal(
        "github",
        f"GitHub refused the merge: {said.said}",
        "it waits for the owner as open; he acts on GitHub or asks for a change",
    )


def answered(
    context: frame.Context, record: Record, intent: MergeIntent, outcome: MergeOutcome
) -> Found:
    """Write what the forge answered the merge call."""
    if isinstance(outcome, MergeDenied):
        raise denied(context, record, intent, outcome)
    if isinstance(outcome, MergeTaken):
        queued = MergeAccepted(
            tip=intent.tip, at=context.world.now, queued=outcome.queued
        )
        return written(context, record, queued)
    number = record.landing.pull.number if record.landing and record.landing.pull else 0
    pull = seen(context.ports.forge.pull(number))
    world = replace(context.world, pull=pull)
    return written(
        context, record, landed(record, world, pull, (intent.by, intent.via))
    )


def called(
    context: frame.Context, record: Record, intent: MergeIntent, subject: str | None
) -> Found:
    """Write the intent, call the forge's merge pinned to its tip, and write the answer."""
    pull = record.landing.pull if record.landing else None
    if pull is None:
        raise Refusal("no-pull", "the task has no pull request", "lem land next SLUG")
    record = context.write(record, partial(changes.landing, intent=intent))
    text = MergeText(subject=subject or pull.title, body="")
    outcome = context.ports.forge.merge(pull.number, intent.tip, "squash", text)
    return answered(context, record, intent, outcome)
