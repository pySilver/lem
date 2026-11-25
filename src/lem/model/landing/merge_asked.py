"""What a merge is asked with, and why it may not go as asked (`landing.md` E, "Stale tap",
"GitHub refuses", "Owner merge refused for the base"; `main:land.expected_refusal`, `cmd_merge`,
`merge_locked`).

The owner's word is for the tip he saw: another tip merges nothing. His standing merge goes
only while it stands. After GitHub refused a tip nobody merges it again unasked: only his word
does. A squash takes the subject of the builder's report, and a merge that keeps the branch's
commits takes none.
"""

import re
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import merge_standing
from lem.model.landing.world import Merger
from lem.records.base import Frozen
from lem.records.landing.merge import Via
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.record import Record

WHOLE = re.compile("[0-9a-f]{40}")
OWNER: Merger = "owner"


class Asked(Frozen, frozen=True, kw_only=True):
    """A merge asked for: who, through what, the whole commit the caller saw, whether it is
    the owner's standing merge, and the subject of the one commit of a squash."""

    by: Merger
    via: Via
    tip: str | None = None
    standing: bool = False
    subject: str | None = None


def tip_why(landing: Landing, asked: Asked) -> str | None:
    """Why the tip the caller saw is not the proposed one: not a whole commit, his standing
    merge that no longer stands, the owner's word for another tip, or another tip."""
    shown = landing.proposed.tip if landing.proposed else None
    tip = asked.tip
    word = asked.by == OWNER and not asked.standing
    found = (
        (
            tip is not None and not WHOLE.fullmatch(tip),
            f"--tip is not a whole commit: {tip}",
        ),
        (
            asked.standing and merge_standing.standing_of(landing) is None,
            f"no merge of the owner's stands for {shown}: the proposal ended it",
        ),
        (
            word and tip != shown,
            f"the owner's merge names {tip}, and the proposal is {shown}",
        ),
        (
            tip is not None and tip != shown,
            f"it was asked for {tip}, and the proposal is {shown}",
        ),
    )
    return next((pair[1] for pair in found if pair[0]), None)


def tip_refusal(record: Record, asked: Asked) -> Refusal | None:
    """Why the merge may not go for the tip the caller saw (`tip_why`)."""
    why = tip_why(record.landing or Landing(), asked)
    if why is None:
        return None
    slug = record.task.slug
    return Refusal(
        "tip",
        f"{why}: nothing was merged",
        f"the owner reads the pull request as it is now (lem land next {slug}), and merges "
        "the tip he saw",
    )


def github_refusal(record: Record, asked: Asked) -> Refusal | None:
    """Why the merge agent and the server do not merge a tip GitHub refused: no automatic
    retry of that tip; the owner's word merges it after he acted on GitHub."""
    landing = record.landing or Landing()
    refused, proposed = landing.refused, landing.proposed
    if asked.by == OWNER and not asked.standing:
        return None
    if refused is None or refused.source != "github" or proposed is None:
        return None
    if refused.tip != proposed.tip:
        return None
    return Refusal(
        "github",
        f"GitHub refused the merge of {refused.tip}: {refused.line}; it is not tried again "
        "unasked",
        "the owner acts on GitHub, then merges it on his word",
    )


def message_refusal(world: World, asked: Asked) -> Refusal | None:
    """Why the subject does not fit `branch.history`: a squash needs it, a merge that keeps
    the branch's commits takes none."""
    squash = world.rules.history == "squash"
    if squash and asked.subject is None:
        why = (
            'branch.history is "squash": the one commit takes the subject of the report'
        )
        fix = "pass --message with the commit subject of the builder's report"
    elif not squash and asked.subject is not None:
        why = (
            'branch.history is "keep": the branch\'s own commits land, with no subject'
        )
        fix = "run it again with no --message"
    else:
        return None
    return Refusal("message", why, fix)


def refusal(record: Record, world: World, asked: Asked) -> Refusal | None:
    """The first reason the merge may not go as asked."""
    return (
        tip_refusal(record, asked)
        or github_refusal(record, asked)
        or message_refusal(world, asked)
    )
