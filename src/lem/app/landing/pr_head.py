"""The head of the pull request's text, on either track, in the order the owner reads it
(`main:land.head_lines`): green, or not green with each reason; the time the task ran without
him; and why it is careful, which makes it his to merge."""

from typing import TYPE_CHECKING

from lem.app.landing.pr_inputs import Block, block
from lem.model.landing import carry, review
from lem.model.landing.green_words import reason

if TYPE_CHECKING:
    from lem.model.landing.propose import Proposal
    from lem.records.record import Record

GREEN = (
    "**Green.** The checks passed with the bar where it was, the review left no "
    "must-fix, no criterion changed, and no decision past the personas was taken "
    "without an answer."
)


def verdict(proposal: Proposal) -> Block:
    """Green, or not green with each reason first."""
    reasons = proposal.proposed.reasons
    if not reasons:
        return Block(lines=(GREEN,))
    return Block(lines=("**Not green.**", "", *(f"- {why}" for why in reasons)))


def alone(record: Record) -> tuple[str, ...]:
    """The line that says the task ran without the owner, and since when: a cause of not
    green only through what was decided then, which the reasons name."""
    task = record.task
    if task.mode != "alone":
        return ()
    since = task.mode_since or task.opened
    stamp = since.strftime("%Y-%m-%d %H:%M UTC")
    return (f"It ran without the owner from {stamp}.",)


def careful(proposal: Proposal) -> tuple[str, ...]:
    """A careful request is a person's to merge, green or not, and he reads why first."""
    if not proposal.careful:
        return ()
    listed = "; ".join(map(reason, proposal.careful))
    return (f"**Careful**, so the owner merges it: {listed}.",)


def code_review(record: Record, proposal: Proposal) -> tuple[str, ...]:
    """What the code review carried over the rebase onto this proposal."""
    landing = record.landing
    if landing is None:
        return ()
    last = review.newest(landing)
    if last is None or carry.source(landing, proposal.proposed) != last.tip:
        return ()
    suffix = ", and its open must-fix" if review.must_fix(last) else ""
    return (f"The review carried over the rebase{suffix}.",)


def carried(proposal: Proposal) -> tuple[str, ...]:
    """What the prior merge read and the owner's approval carry into this proposal."""
    made = proposal.proposed
    shown = (made.merge_review_why,) if made.merge_review_why else ()
    owner = made.owner_merge
    if owner is None:
        return shown
    how = "stands" if owner.state == "stands" else "ended"
    return (*shown, f"The owner's merge {how}: {owner.why}.")


def blocks(record: Record, proposal: Proposal) -> tuple[Block, ...]:
    """The head's blocks."""
    without = block(None, alone(record))
    return (
        verdict(proposal),
        *without,
        *block(
            None, careful(proposal) + code_review(record, proposal) + carried(proposal)
        ),
    )
