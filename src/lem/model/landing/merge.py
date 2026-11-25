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

from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.model.landing import merge_asked, merge_evidence, merge_lines, mergeread
from lem.model.landing.review import newest
from lem.model.landing.world import Due, Merger, World
from lem.records.base import Frozen
from lem.records.landing.merge import MergeIntent
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.propose import Proposed
    from lem.records.record import Record

STEP = "merge"
# How the forge lands the branch: one squashed commit, or its own commits replayed.
type Method = Literal["squash", "rebase"]
OWNER: Merger = "owner"


class Merging(Frozen, frozen=True, kw_only=True):
    """The merge to call: its intent, the forge's method, and the one commit's subject and
    body (a squash's; a rebase lands the branch's own commits)."""

    intent: MergeIntent
    method: Method
    subject: str
    body: str


def who(world: World, reasons: tuple[str, ...]) -> Merger:
    """Who merges a proposal: the merge agent for a green request the settings let it merge,
    else the owner."""
    if reasons or world.rules.land == OWNER:
        return OWNER
    return "merger"


def authority(record: Record, world: World) -> str | None:
    """Why the merge agent may not merge, or None when it may (`main:land.merger_refusal`)."""
    landing = record.landing or Landing()
    proposed, shape = landing.proposed, record.task.shape
    last, read = newest(landing), mergeread.usable(landing, world)
    if proposed is None or proposed.reasons:
        return "the request is not green, so the owner merges it"
    if proposed.careful or (shape is not None and shape.careful):
        return "the request is careful: the owner merges it, whatever the settings say"
    if last is None or last.careful is None:
        return "no review that answered made the careful call for this change"
    if who(world, proposed.reasons) == OWNER:
        return (
            'branch.land is "owner" in .lem/settings.toml: the owner merges every task'
        )
    if read is None or read.verdict != "merge":
        return "the merge agent's read of this tip and base calls the owner"
    return None


def due(record: Record, world: World) -> Due:
    """The merge, and who merges it: the merge agent, the owner's standing merge, which the
    board's server carries out, or the owner's word."""
    why = authority(record, world)
    if why is None:
        return Due(step=STEP, why="the merge agent's read says merge", by="merger")
    if merge_evidence.standing_of(record.landing or Landing()) is not None:
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


def merging(record: Record, world: World, intent: MergeIntent, subject: str) -> Merging:
    """The call for `intent`: a squash with the report's `subject` and a body that names the
    task, and the line of a merge on a base a safe read covered; or a rebase that keeps the
    branch's commits."""
    if world.rules.history == "keep":
        return Merging(intent=intent, method="rebase", subject="", body="")
    landing = record.landing or Landing()
    read, checked = mergeread.usable(landing, world), landing.checked
    line = None
    if read is not None and read.base_call == "safe" and checked is not None:
        bases = (checked.base, world.base)
        line = merge_lines.base_line(world.rules.base, bases, read.why or "")
    body = merge_lines.squash_body(record.task.slug, line)
    return Merging(intent=intent, method="squash", subject=subject, body=body)


def decide(
    record: Record, world: World, asked: merge_asked.Asked, checks_tree: str
) -> Refusal | Merging:
    """The merge to call for `asked`, or why it may not go to the forge with the world as it
    is now; `checks_tree` is the tree of the base the checks ran on."""
    proposed = opened(record)
    if isinstance(proposed, Refusal):
        return proposed
    refused = (
        merge_evidence.base_side(record, world, checks_tree)
        or merge_evidence.forge_side(record, world, proposed)
        or merge_evidence.our_side(record, world, proposed)
        or merge_asked.refusal(record, world, asked)
    )
    if refused is not None:
        return refused
    why = None if asked.by == OWNER else authority(record, world)
    if why is not None:
        return Refusal(
            "merger-rule",
            f"the merge agent may not merge: {why}",
            "the owner merges it, on his word",
        )
    intent = MergeIntent(tip=proposed.tip, by=asked.by, via=asked.via, at=world.now)
    return merging(record, world, intent, asked.subject or "")
