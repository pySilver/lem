"""The merge call on record, while GitHub has it or the reply is missing."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import merge, merge_evidence
from lem.records.landing.merge import MergeAccepted, MergeIntent

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.records.record import Record


def current(record: Record) -> MergeIntent | MergeAccepted | None:
    """What the landing recorded before the call or when GitHub took it."""
    landing = record.landing
    if record.task.status != "open" or landing is None:
        return None
    return landing.intent or landing.accepted


def said(record: Record) -> str | None:
    """What the owner sees while the board offers no new merge."""
    match current(record):
        case MergeIntent():
            return "Check the pull request on GitHub"
        case MergeAccepted():
            return "GitHub has the merge in its queue."
    return None


def proposal_refusal(seen: Seen) -> Refusal | None:
    """The landing's refusal from the proposal and the branch facts the board knows."""
    record = seen.record
    proposed = merge.opened(record)
    if isinstance(proposed, Refusal):
        return proposed
    tip = seen.head.sha if seen.head else proposed.tip
    return merge_evidence.careful_refusal(record) or merge_evidence.changed_tip(
        record, proposed, tip
    )


def proposal_fix(seen: Seen) -> str | None:
    """What the owner does when the pull request cannot merge as proposed."""
    if seen.record.task.status != "open":
        return None
    refused = proposal_refusal(seen)
    return None if refused is None else f"{refused.why}. {refused.fix}."
