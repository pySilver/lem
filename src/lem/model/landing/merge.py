"""`merge`: the merge of the open pull request, by the merge agent or on the owner's word
(`landing.md` C, "In `open`"; H 2).

A merge is an intent written before the forge's call; under the merge lock an intent on record
is reconciled before any new call (`reconcile.py`), and the evidence is read again
(`merge_evidence.py`). The plain path merges by squash; a merge that keeps the branch's commits,
his standing merge and the safe read of a moved base are the step `land-merge`'s.
"""

from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.model.landing import merge_evidence, mergeread
from lem.model.landing.world import Due, Merger, World, later
from lem.records.landing.merge import MergeIntent
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.propose import Proposed
    from lem.records.record import Record

STEP = "merge"
OWNER: Merger = "owner"
type Via = Literal["session", "server"]


def who(world: World, reasons: tuple[str, ...]) -> Merger:
    """Who merges a proposal: the merge agent for a green request the settings let it merge,
    else the owner."""
    if reasons or world.rules.land == OWNER:
        return OWNER
    return "merger"


def authority(record: Record, world: World) -> str | None:
    """Why the merge agent may not merge, or None when it may: a green request that is not
    careful, the settings' word that the agent lands, and its read that says merge for this
    tip and base (`main:land.merger_refusal`)."""
    landing = record.landing or Landing()
    proposed, shape = landing.proposed, record.task.shape
    read = mergeread.usable(landing, world)
    if proposed is None or proposed.reasons:
        return "the pull request is not green"
    if proposed.careful or (shape is not None and shape.careful):
        return "the request is careful: the owner merges it"
    if who(world, proposed.reasons) == OWNER:
        return "branch.land is owner: the owner merges each pull request"
    if read is None or read.verdict != "merge":
        return "the merge agent's read of this tip and base calls the owner"
    return None


def due(record: Record, world: World) -> Due:
    """The merge, and who merges it."""
    why = authority(record, world)
    if why is None:
        return Due(step=STEP, why="the merge agent's read says merge", by="merger")
    return Due(step=STEP, why=f"the owner merges it: {why}", by="owner")


def authorized(
    record: Record, world: World, by: Merger, tip: str | None
) -> Refusal | None:
    """Why `by` may not merge the proposed tip: the merge agent without its authority, or the
    owner's word for a tip that is not the proposed one (a stale tap)."""
    proposed = (record.landing or Landing()).proposed
    shown = proposed.tip if proposed else None
    if by == "owner" and tip != shown:
        return Refusal(
            "tip",
            f"the owner's merge names {tip}, and the proposal is {shown}",
            "the owner reads the pull request as it is now, and merges that tip",
        )
    why = authority(record, world) if by == "merger" else None
    if why is not None:
        return Refusal(
            "merger-rule",
            f"the merge agent may not merge: {why}",
            "the owner merges it, on his word",
        )
    return None


def opened(record: Record) -> Refusal | Proposed:
    """The proposal of an open task, or why there is none to merge."""
    slug, status = record.task.slug, record.task.status
    proposed = (record.landing or Landing()).proposed
    if status != "open" or proposed is None:
        return Refusal(
            "status",
            f"{slug} is {status}, with no open pull request",
            f"lem land next {slug}",
        )
    return proposed


def decide(
    record: Record, world: World, by: Merger, call: tuple[Via, str | None]
) -> Refusal | MergeIntent:
    """The intent of the merge `by` asks for, through `call` (where it was asked, and the tip
    the caller saw), or why it may not go to the forge."""
    proposed = opened(record)
    if isinstance(proposed, Refusal):
        return proposed
    if world.rules.history == "keep":
        return later("a merge that keeps the branch's commits", "land-merge")
    via, seen = call
    refused = merge_evidence.stale(record, world, proposed) or authorized(
        record, world, by, seen
    )
    if refused is not None:
        return refused
    return MergeIntent(tip=proposed.tip, by=by, via=via, at=world.now)
