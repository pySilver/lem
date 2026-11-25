"""`merge`: the merge of the open pull request, by the merge agent or on the owner's word
(`landing.md` C, "In `open`"; D, the standing merge and the safe read; H 2).

A merge is an intent written before the forge's call; under the merge lock an intent on record
is reconciled before any new call (`reconcile.py`), and the evidence is read again
(`merge_evidence.py`). The merge agent merges a green request that is not careful, which the
newest review made the careful call on, where the settings let it, on its read's `merge` for the
tip and base. The owner's word merges the tip he saw (`merge_asked.py`), and his merge that a
moved base refused stands until a safe read. `branch.history` squashes the branch into one
commit, or lands its own commits (a rebase on the forge).
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import (
    merge_asked,
    merge_call,
    merge_evidence,
    merge_standing,
    mergeread,
)
from lem.model.landing.careful_words import owner_says
from lem.model.landing.review import newest
from lem.model.landing.world import Due, Merger, World
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.propose import Proposed
    from lem.records.record import Record

STEP = "merge"
NOT_GREEN = "the request is not green, so the owner merges it"
CAREFUL = "the request is careful: the owner merges it, whatever the settings say"
NO_CALL = "no review that answered made the careful call for this change"
LAND_OWNER = 'branch.land is "owner" in .lem/settings.toml: the owner merges every task'
CALLS = "the merge agent's read of this tip and base calls the owner"
MOVED = "the criteria were approved again after the proposal, which was made for others"
OWNER: Merger = "owner"


def who(world: World, reasons: tuple[str, ...]) -> Merger:
    """Who merges a proposal: the merge agent for a green request the settings let it merge,
    else the owner."""
    if reasons or world.rules.land == OWNER:
        return OWNER
    return "merger"


def careful(record: Record) -> bool:
    """Whether the proposal, the shape or the owner's word makes the request careful."""
    proposed, shape = (record.landing or Landing()).proposed, record.task.shape
    return (
        bool(proposed and proposed.careful)
        or bool(shape and shape.careful)
        or bool(owner_says(record, owner=False))
    )


def authority(record: Record, world: World, *, verdict: bool = True) -> str | None:
    """Why the merge agent may not merge, or None when it may (`main:land.merger_refusal`):
    the reasons it is not green read again now, careful, no careful call, the settings, and,
    with `verdict`, the read that covers origin's base now, one read for the tip and that
    base. Without `verdict` it is what the merge agent's brief says before it reads."""
    landing = record.landing or Landing()
    last, read = newest(landing), mergeread.latest(landing, world.base_tree)
    found = (
        (careful(record), CAREFUL),
        (
            landing.proposed is None or bool(merge_standing.reasons_now(record, world)),
            NOT_GREEN,
        ),
        (merge_asked.contract_moved(record), MOVED),
        (last is None or last.careful is None, NO_CALL),
        (world.rules.land == OWNER, LAND_OWNER),
        (verdict and (read is None or read.verdict != "merge"), CALLS),
    )
    return next((pair[1] for pair in found if pair[0]), None)


def due(record: Record, world: World) -> Due:
    """The merge, and who merges it: the merge agent, the owner's standing merge, which the
    board's server carries out, or the owner's word."""
    why = authority(record, world)
    if why is None:
        return Due(step=STEP, why="the merge agent's read says merge", by="merger")
    if merge_standing.standing_of(record, world) is not None:
        slug = record.task.slug
        said = (
            "the owner's merge stands: the board's server merges it "
            f"(lem land merge {slug} --by owner --via server --standing)"
        )
        return Due(step=STEP, why=said, by=OWNER)
    return Due(step=STEP, why=f"the owner merges it: {why}", by=OWNER)


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


def merger_refusal(
    record: Record, world: World, asked: merge_asked.Asked
) -> Refusal | None:
    """Why the merge agent may not merge what it asks to: no authority of its own."""
    if asked.by == OWNER:
        return None
    why = authority(record, world)
    if why is None:
        return None
    return Refusal(
        "merger-rule",
        f"the merge agent may not merge: {why}",
        "the owner merges it, on his word",
    )


def decide(
    record: Record, world: World, asked: merge_asked.Asked, checks_tree: str
) -> Refusal | merge_call.Merging:
    """The merge to call for `asked`, or why it may not go to the forge with the world as it
    is now; `checks_tree` is the tree of the base the checks ran on. What was asked (the tip
    the owner saw, his standing merge) is checked before any evidence, so that no refusal of
    an ask that does not hold can keep his merge standing (`main:land.cmd_merge`)."""
    proposed = merge_evidence.new_call_refusal(record) or opened(record)
    if isinstance(proposed, Refusal):
        return proposed
    asked_now = merge_asked.refusal(record, world, asked)
    refused = asked_now or (
        merge_evidence.base_side(record, world, checks_tree)
        or merge_evidence.forge_side(record, world, proposed)
        or merge_evidence.our_side(record, world, proposed)
    )
    refused = refused or merger_refusal(record, world, asked)
    if refused is not None:
        return refused
    return merge_call.merging(record, world, asked, proposed.tip)
