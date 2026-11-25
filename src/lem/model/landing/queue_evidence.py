"""Which forge queue events can answer a recorded merge call."""

from typing import TYPE_CHECKING, Literal

from lem.records.base import Frozen, Moment, Sha
from lem.records.landing.merge import MergeAccepted

if TYPE_CHECKING:
    from lem.model.landing.world import PullSeen
    from lem.records.landing.merge import MergeIntent
    from lem.records.landing.record import Landing

type Call = MergeAccepted | MergeIntent
type Outcome = Literal["queued", "dequeued"]


class Event(Frozen, frozen=True, kw_only=True):
    """The forge's identity and time for one queue event."""

    id: str
    at: Moment
    head: Sha | None = None


def after(event: Event | None, call: Call) -> bool:
    """Whether the event came after the call's last observed event and at its time or later."""
    if event is None or event.id == call.queue_before:
        return False
    if event.at == call.at:
        return call.queue_before is not None
    return event.at > call.at


def matched(pull: PullSeen, call: Call) -> bool:
    """Whether the evidence is for the recorded call and the head it named."""
    event = pull.queue_event
    if pull.state != "open" or event is None or not after(event, call):
        return False
    if (event.head or pull.head) != call.tip:
        return False
    if pull.queued or isinstance(call, MergeAccepted):
        return True
    return after(pull.queue_entered, call)


def action(landing: Landing, pull: PullSeen | None) -> Outcome | None:
    """The queue evidence the landing can use for its current call."""
    call = landing.intent or landing.accepted
    if pull is None or call is None or not matched(pull, call):
        return None
    if pull.queued:
        return None if landing.intent is None else "queued"
    return "dequeued" if pull.dequeued else None
