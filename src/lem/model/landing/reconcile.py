"""The merge as the forge shows it after a call, after a stop around the call, or after a merge
on GitHub (`landing.md` C, "In `open`"; E, "Stop or lost reply around the merge call", "Forge
took the call, not merged yet", "Retarget after the locked read", "Merge on GitHub between look
and call", "Closed on GitHub").

An intent on record is replaced by what the forge shows: the merge, a queue that took the call,
a definite refusal, or the end of a request closed with no merge. With only an open pull request
visible the intent stays, and the owner checks GitHub: a new call goes only on his word. A merge
into another branch than the task's base is no landing. A merge whose base on the forge neither
the checks nor a safe read covered lands, with a line that says so.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import merge_lines, mergeread, reconcile_queue
from lem.model.landing.invariants import target
from lem.model.landing.world import Due, Merger, PullSeen, World
from lem.records.base import Frozen, Sha
from lem.records.landing.merge import MergeAccepted, Merged, MergeIntent, Refused, Via
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.record import Record

# Who refused a merge kept for its tip, as the due step says it.
SAID = MappingProxyType(
    {
        "lem": "Lem refused the merge agent's merge",
        "github": "GitHub refused the merge",
    }
)
type Found = Merged | MergeAccepted | Refused | None


class Trees(Frozen, frozen=True, kw_only=True):
    """The trees a merge is judged by, read from git: of the base the checks ran on, and of
    the commit of the base the merge went onto."""

    checks: Sha
    parent: Sha


def pending(landing: Landing, world: World) -> Due | None:
    """What a merge call left, which comes before anything else of an open request: an
    intent to reconcile, a merge into another base that waits for the owner, the forge's
    merge, queue or end to write down, or a refusal kept for this tip, GitHub's or Lem's of
    the merge agent's merge, after which only the owner's word merges it."""
    pull = world.pull
    refused = refusal_for_tip(landing)
    intent = reconcile_queue.intent_pending(landing, pull)
    if intent is not None:
        return intent
    elsewhere = (
        pull is not None and pull.state == "merged" and pull.base != world.rules.base
    )
    if refused is not None and elsewhere and landing.intent is None:
        return Due(step="wait", why=refused.line)
    if landing.accepted is not None or (pull is not None and pull.state != "open"):
        return Due(step="merged", why="the forge took the merge, or ended the request")
    if refused is None or refused.kind == "base":
        return None
    said = SAID[refused.source]
    return Due(
        step="merge",
        why=f"{said} of this tip: {refused.line}; the owner's word merges it",
        by="owner",
    )


def line_of(
    landing: Landing, merged: Merged, trees: Trees, base: str
) -> tuple[str | None, bool]:
    """The line a merge leaves in the pull request's text, and whether no read covered its
    base: no line on the checks' own base (by its tree), the safe read's line on a base it
    covered, else the line that no read covered it."""
    warning = merge_lines.head_warning(landing, merged)
    if warning is not None:
        return warning, True
    if trees.parent == trees.checks:
        return None, False
    safe = [
        read
        for read in landing.reads
        if read.tip == merged.merged_head and read.base_call == "safe"
    ]
    bases = (merged.base_checked, merged.parent)
    covering = [read.why or "" for read in safe if read.base_tree == trees.parent]
    if covering:
        return merge_lines.base_line(base, bases, covering[-1]), False
    read = safe[-1].base if safe else None
    return merge_lines.uncovered_line(base, bases, read), True


def made(
    landing: Landing,
    world: World,
    pull: PullSeen,
    who: tuple[Merger, Via],
    trees: Trees,
) -> Merged:
    """The record of a merge the forge reports whole, into the task's base, by `who` (who
    merged and through what), judged by `trees`."""
    read = mergeread.latest(landing, world.base_tree)
    merged = Merged(
        by=who[0],
        via=who[1],
        commit=pull.merge_commit or "",
        merged_head=pull.merged_head or "",
        parent=pull.base_parent or "",
        destination=pull.base,
        base_checked=landing.checked.base
        if landing.checked
        else pull.base_parent or "",
        base_merged=pull.base_parent or "",
        base_read=read.base if read else None,
        at=world.now,
    )
    line, uncovered = line_of(landing, merged, trees, world.rules.base)
    return replace(
        merged, uncovered=line if uncovered else None, text_updated=line is None
    )


def landed(
    record: Record, world: World, pull: PullSeen, facts: tuple[Merger, Via, Trees]
) -> Refusal | Merged:
    """The merge the forge shows, to record (`facts`: who merged, through what, and the
    trees it is judged by), or why it is no landing: another destination, which leaves the
    task open with nothing cleaned, or a merge whose commit the forge does not report yet."""
    wrong = target(pull.base, world.rules, pull.url)
    slug = record.task.slug
    if wrong is not None:
        return wrong
    if not (pull.merge_commit and pull.merged_head and pull.base_parent):
        return Refusal(
            "unreported",
            f"GitHub merged {pull.url} and does not report its commit yet: nothing was "
            "written",
            f"lem land merged {slug} runs again in a minute",
        )
    landing = record.landing or Landing()
    who = (
        reconcile_queue.author(landing, pull)
        if landing.intent or landing.accepted
        else facts[:2]
    )
    return made(landing, world, pull, who, facts[2])


def reconciled(
    record: Record,
    world: World,
    intent: MergeIntent,
    trees: Trees,
) -> Refusal | Found:
    """What an intent on record becomes, by what the forge shows now: the merge, the queue
    that took it, the queue's end in GitHub's words, None for a request closed with no
    merge (whose end `merged` writes), or the refusal that keeps it while only an open pull
    request is visible."""
    pull = world.pull
    if pull is not None and pull.state == "merged":
        return landed(record, world, pull, (intent.by, intent.via, trees))
    if pull is not None and pull.state == "closed":
        return None
    return reconcile_queue.answer(record, world, intent)


def refusal_for_tip(landing: Landing) -> Refused | None:
    """The refusal for the tip the task proposes."""
    refused, proposed = landing.refused, landing.proposed
    if refused is not None and proposed is not None and refused.tip == proposed.tip:
        return refused
    return None
