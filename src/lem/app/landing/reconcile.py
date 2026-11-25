"""What a merge left, written down: the forge's merge, its queue, its refusal in its own words,
a request it closed, a merge into another base, and what a refusal for a moved base keeps
(`landing.md` C, "In `open`"; E, the merge's rows). The call itself is `merge_called.py`.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes
from lem.kernel.errors import Refusal
from lem.model.landing import merge_standing
from lem.records.journal.merge import MergeNoted, RefusalNoted
from lem.records.landing.merge import MergeAccepted, Merged, Refused

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.merge_asked import Asked
    from lem.model.landing.world import Merger
    from lem.records.record import Record

type Found = Merged | MergeAccepted | Refused | None


def taken(record: Record, *, found: Merged | MergeAccepted | Refused) -> Record:
    """The record with what the forge did of the call, the intent cleared: the merge, the
    queue that took it, or a refusal kept for its tip, with its note in the journal."""
    if isinstance(found, MergeAccepted):
        return changes.landing(record, accepted=found, intent=None)
    if isinstance(found, Refused):
        changed = changes.landing(record, refused=found, intent=None, accepted=None)
        return changes.noted(changed, RefusalNoted(at=found.at, refusal=found))
    changed = changes.landing(
        record, merged=found, intent=None, accepted=None, phase="merged"
    )
    return changes.noted(changed, MergeNoted(at=found.at, merged=found))


def refused(context: Context, record: Record, found: Refused) -> Refusal:
    """Write GitHub's refusal in its words, kept for its tip, and give the step's: no
    automatic retry of that tip, and the owner's word merges it after he acted on GitHub."""
    context.write(record, partial(taken, found=found))
    slug = record.task.slug
    return Refusal(
        "github",
        f"GitHub refused the merge of {found.tip}: {found.line}",
        f"it waits for the owner as open: he acts on GitHub, then lem land merge {slug} "
        f"--by owner --tip {found.tip}",
    )


def written(
    context: Context, record: Record, found: Found | Refusal, by: Merger
) -> object:
    """Write what the forge shows (`by`: who asked for the merge), or raise why nothing more
    is written: a merge into another base keeps Lem's refusal for the tip, a queue's end or
    GitHub's refusal keeps GitHub's words, and a request closed with no merge clears the
    intent for `merged`, which ends the task."""
    landing = record.landing
    tip = landing.proposed.tip if landing and landing.proposed else ""
    if isinstance(found, Refusal):
        if found.code == "target":
            kept = Refused(
                tip=tip,
                source="lem",
                kind="target",
                line=found.why,
                by=by,
                at=context.world.now,
            )
            context.write(record, partial(taken, found=kept))
        raise found
    if isinstance(found, Refused):
        raise refused(context, record, found)
    if found is None:
        context.write(record, partial(changes.landing, intent=None))
        return context.world.pull
    context.write(record, partial(taken, found=found))
    return found


def kept(context: Context, record: Record, refusal: Refusal, asked: Asked) -> Refusal:
    """Keep what a refusal of the merge for the base keeps, Lem's refusal of the tip and the
    owner's merge standing, and give the refusal (`main:land.cmd_merge`)."""
    landing = record.landing
    if landing is None:
        return refusal
    held = merge_standing.kept(
        landing, refusal, (asked.by, asked.via), context.world.now
    )
    if held is None:
        return refusal
    keep, standing = held
    after = context.write(record, partial(taken, found=keep))
    if standing is not None and merge_standing.standing_of(landing) is None:
        context.write(after, partial(changes.landing, standing=standing))
    return refusal
