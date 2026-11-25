"""The merge call on record, while GitHub has it or the reply is missing."""

from typing import TYPE_CHECKING

from lem.records.landing.merge import MergeAccepted, MergeIntent

if TYPE_CHECKING:
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
