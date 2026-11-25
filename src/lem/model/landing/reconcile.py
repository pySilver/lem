"""The merge as the forge shows it after a call, or after a stop around the call (`landing.md`
C, "In `open`"; E, "Stop or lost reply around the merge call").

An intent on record is replaced by what the forge shows: the merge, a queue that took the call,
or nothing yet. With only an open pull request visible the intent stays, and the owner checks
GitHub: a new call goes only on his word. The plain path edits no pull request's text after the
merge, so a merge is written with `text_updated` false. A closed request, a retarget after the
read and that edit are the step `land-merge`'s.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import mergeread
from lem.model.landing.world import Due, Merger, PullSeen, World, later
from lem.records.landing.merge import MergeAccepted, Merged, MergeIntent, Via
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.record import Record


def pending(landing: Landing, world: World) -> Due | None:
    """What a merge call left, which comes before anything else of an open request: an
    intent to reconcile, the forge's merge or queue to write down, or GitHub's refusal of this
    tip, which waits for the owner (no automatic retry)."""
    pull, proposed, refused = world.pull, landing.proposed, landing.refused
    if landing.intent is not None:
        why = "a merge call is on record: it is reconciled first"
        return Due(step="merge", why=why, by=landing.intent.by)
    if landing.accepted is not None or (pull is not None and pull.state != "open"):
        return Due(step="merged", why="the forge took the merge, or ended the request")
    if refused is None or proposed is None or refused.tip != proposed.tip:
        return None
    why = f"GitHub refused the merge of this tip: {refused.line}"
    return Due(step="wait", why=f"{why}; the owner acts on GitHub or asks for a change")


def uncovered(landing: Landing, parent: str) -> str | None:
    """The line for a merge onto a base that neither the checks nor the merge read covered."""
    checked = landing.checked
    read = mergeread.read_of(landing)
    covered = {checked.base if checked else None, read.base if read else None}
    if parent in covered:
        return None
    return f"the merge went onto {parent}, a base that neither the checks nor the read covered"


def landed(
    record: Record, world: World, pull: PullSeen, who: tuple[Merger, Via]
) -> Refusal | Merged:
    """The merge the forge shows, to record, by `who` (who merged and through what)."""
    landing = record.landing or Landing()
    checked = landing.checked
    if pull.base != world.rules.base:
        return later(f"a merge into {pull.base}, not the task's base", "land-merge")
    if not (pull.merge_commit and pull.merged_head and pull.base_parent and checked):
        return later("a merge whose commit the forge does not report", "land-merge")
    read = mergeread.read_of(landing)
    return Merged(
        by=who[0],
        via=who[1],
        commit=pull.merge_commit,
        merged_head=pull.merged_head,
        parent=pull.base_parent,
        destination=pull.base,
        base_checked=checked.base,
        base_merged=pull.base_parent,
        base_read=read.base if read else None,
        uncovered=uncovered(landing, pull.base_parent),
        text_updated=False,
        at=world.now,
    )


def reconciled(
    record: Record, world: World, intent: MergeIntent
) -> Refusal | Merged | MergeAccepted:
    """What an intent on record becomes, by what the forge shows now."""
    pull = world.pull
    if pull is not None and pull.state == "merged":
        return landed(record, world, pull, (intent.by, intent.via))
    if pull is not None and pull.state == "open" and pull.queued:
        return MergeAccepted(tip=intent.tip, at=world.now, queued=pull.queued)
    if pull is not None and pull.state == "open":
        return Refusal(
            "intent",
            f"a merge call for {intent.tip} went out, and GitHub shows the pull request "
            "open: the call may not have reached it",
            f"the owner checks {pull.url} on GitHub; a new call goes only on his word "
            "after that check (the step `land-merge` builds it)",
        )
    return later("a pull request closed after a merge call", "land-merge")
