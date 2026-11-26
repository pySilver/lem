"""The result of a recorded merge call that GitHub put in a queue."""

from typing import TYPE_CHECKING

from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.landing import queue_evidence
from lem.model.landing.world import Due
from lem.records.landing.merge import MergeAccepted, Refused
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.world import PullSeen, World
    from lem.records.landing.merge import MergeIntent, Merger, Via
    from lem.records.record import Record


def accepted(intent: MergeIntent, queue: str) -> MergeAccepted:
    """Keep the call's identity when GitHub takes the merge."""
    return MergeAccepted(
        tip=intent.tip,
        at=intent.at,
        queued=queue,
        by=intent.by,
        via=intent.via,
        queue_before=intent.queue_before,
    )


def removed(call: queue_evidence.Call, world: World, by: Merger) -> Refused | None:
    """A confirmed removal of the recorded call, in GitHub's words."""
    pull = world.pull
    if pull is None or pull.queued or not pull.dequeued:
        return None
    if not queue_evidence.matched(pull, call):
        return None
    return Refused(
        tip=call.tip,
        source="github",
        kind="rule",
        line=pull.dequeued,
        by=by,
        at=world.now,
    )


def queued(record: Record, world: World) -> Refusal | Refused:
    """What a pull request the forge holds in its queue shows while it is open."""
    landing = record.landing or Landing()
    waiting = landing.accepted
    if waiting is not None:
        found = removed(waiting, world, requester(landing))
        if found is not None:
            return found
    slug = record.task.slug
    # An open pull without an intent reaches this step only for an accepted call.
    tip = waiting.tip if waiting else world.tip or ""  # pragma: no mutate
    return Refusal(
        "queued",
        f"GitHub holds the merge of {tip} in its queue, and has not merged it yet",
        f"lem land merged {slug} runs again once GitHub merged it",
    )


def requester(landing: Landing) -> Merger:
    """Who asked for a queued merge; older acceptances carry only the proposal."""
    if landing.accepted and landing.accepted.by:
        return landing.accepted.by
    # A call is recorded only for a proposal and keeps that proposal while queued.
    proposed = landing.proposed
    return proposed.who_acts if proposed else "owner"  # pragma: no mutate


def author(landing: Landing, pull: PullSeen) -> tuple[Merger, Via]:
    """Attribute the merge to a recorded call only for the exact head it named."""
    call = landing.intent or landing.accepted
    if call is not None and call.tip == pull.merged_head:
        return call.by or "owner", call.via or "github"
    return "owner", "github"


def intent_pending(landing: Landing, pull: PullSeen | None) -> Due | None:
    """A lost reply needs its queue result or the owner's check of GitHub."""
    intent = landing.intent
    if intent is None or (pull is not None and pull.state != "open"):
        return None
    if queue_evidence.action(landing, pull) is not None:
        return Due(step="merged", why="the forge reports the queue's answer")
    return Due(
        step="merge",
        why="a merge call is on record: it is reconciled first",
        by=intent.by,
    )


def answer(
    record: Record, world: World, intent: MergeIntent
) -> MergeAccepted | Refused | Refusal:
    """The queue's answer after a lost reply, or the refusal that keeps the intent."""
    pull = world.pull
    if pull is not None and pull.queued and queue_evidence.matched(pull, intent):
        return accepted(intent, pull.queued)
    ended = removed(intent, world, intent.by)
    if ended is not None:
        return ended
    url = pull.url if pull else "the pull request"
    slug, stamp = record.task.slug, clock.compact(intent.at)
    return Refusal(
        "intent",
        f"a merge call for {intent.tip} went out at {stamp}, and GitHub shows {url} open: "
        "the call may not have reached it, and no new call goes unasked",
        f"the owner checks {url} on GitHub; when it is not merged there, his word merges it: "
        f"lem land merge {slug} --by owner --tip {intent.tip} --checked {stamp}",
    )
