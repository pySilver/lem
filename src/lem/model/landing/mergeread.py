"""`merge-review`: the merge agent's read of the proposed tip on a base (`landing.md` C, "In
`open`"; D, the merge read's carry and the safe read on a moved base; E, "Base moved, open PR",
"Two unusable answers", "No answer").

A read covers the base its brief named, by that base's tree: a later move of origin's base
covers nothing, and an empty commit or a revert to the same tree moves nothing. A read settles
the question of its tip and base when it gave a verdict, or when it is the second answer that
could not be recorded: on a base that did not move it calls the owner with no verdict, on a
moved base it is another round (`main:land.unread_next`). A read of the tip that says another
round is answered by a new round alone.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import merge_said
from lem.records.base import Frozen, Moment, Sha
from lem.records.landing.propose import MergeRead
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.record import Record

STEP = "merge-review"
ROUND = merge_said.ROUND


class Briefed(Frozen, frozen=True, kw_only=True):
    """The brief a reply answers: its tip and base, the tree of that base, and whether that
    tree is not the tree of the base the checks ran on (a moved base)."""

    tip: Sha
    base: Sha
    base_tree: Sha
    moved: bool


def settled(read: MergeRead) -> bool:
    """Whether a read answers its tip and base for good: a verdict, another round, or the
    second answer that could not be recorded."""
    return (
        read.verdict is not None
        or read.base_call == ROUND
        or read.attempts >= merge_said.TRIES
    )


def another_round(landing: Landing) -> MergeRead | None:
    """The read of the proposed tip that says another round, which only a new round
    answers."""
    tip = landing.proposed.tip if landing.proposed else None
    found = [
        read for read in landing.reads if read.tip == tip and read.base_call == ROUND
    ]
    return found[-1] if found else None


def latest(landing: Landing, tree: str | None = None) -> MergeRead | None:
    """The newest settled read of the proposed tip: of a base with the tree `tree` (the read
    that covers origin's base as it is now), or of any base (the merge agent's word for the
    tip, beside which a merge on a moved base needs a safe read of that base)."""
    tip = landing.proposed.tip if landing.proposed else None
    found = [
        read
        for read in landing.reads
        if read.tip == tip and settled(read) and tree in {None, read.base_tree}
    ]
    return found[-1] if found else None


def made(
    landing: Landing, briefed: Briefed, reply: str | None, now: Moment
) -> MergeRead:
    """The read of `reply` to the brief `briefed`: a verdict with its why, or an answer that
    could not be recorded, the first or the second, which settles."""
    read = MergeRead(
        tip=briefed.tip,
        base=briefed.base,
        base_tree=briefed.base_tree,
        no_answer=reply is None,
        at=now,
    )
    problem = merge_said.problem_of(reply, moved=briefed.moved)
    if reply is not None and problem is None:
        return merge_said.answered(read, reply, moved=briefed.moved)
    count = 1 + sum(
        not settled(earlier)
        for earlier in landing.reads
        if (earlier.tip, earlier.base) == (briefed.tip, briefed.base)
    )
    said = (reply, problem or "")
    return merge_said.unrecorded(read, said, count=count, moved=briefed.moved)


def decide(
    record: Record, briefed: Briefed, reply: str | None, now: Moment
) -> Refusal | MergeRead:
    """The read to record for the reply to the brief `briefed`, or why it is refused: no
    proposal, a reply of a brief of another tip, or a tip whose read said another round."""
    landing = record.landing or Landing()
    slug = record.task.slug
    shown = landing.proposed.tip if landing.proposed else None
    if shown is None:
        return Refusal(
            "no-pull",
            f"{slug} proposes no pull request yet",
            f"lem land propose {slug} comes first",
        )
    if briefed.tip != shown:
        return Refusal(
            "old-tip",
            f"the reply is of the brief of {briefed.tip}, and the proposal is {shown} now: "
            "it read an earlier proposal, and it is not written down",
            f"lem land merge-review {slug} writes the brief of this one, and a fresh merge "
            "agent reads it",
        )
    if another_round(landing) is not None:
        return Refusal(
            "another-round",
            f"the merge agent's read of {shown} said that the moved base needs another round "
            "of the checks, and no later read answers that",
            f"lem land next {slug} names the new round",
        )
    return made(landing, briefed, reply, now)


def again(read: MergeRead) -> Refusal | None:
    """The refusal after a first answer that could not be recorded, which a fresh merge
    agent answers again; None for a read that settles."""
    if settled(read):
        return None
    return Refusal(
        "no-verdict",
        f"the merge agent's answer was not recorded: {read.why}; the merge agent is asked "
        "again",
        "a fresh merge agent reads the same brief, and its reply is written down with the "
        "same --tip and --base",
    )
