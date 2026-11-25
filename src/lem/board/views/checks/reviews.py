"""The card of the review on the tab Checks and review (`board_task.checks_tab` on `main`): each
round with who answered, who was silent and why, the profiles it ran and left out and the commit
it read; then the proposal, green with what green means or not green with its reasons."""

from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.names import plural
from lem.board.inputs.parts import Row
from lem.board.inputs.task.checks import Proposal
from lem.board.views import rounds
from lem.board.views.reasons import reasons

if TYPE_CHECKING:
    from lem.board.views.world import World
    from lem.records.landing.review import Named, Reviewed
    from lem.records.record import Record

# What green means, as the proposal says it.
GREEN = (
    "the checks passed with the bar where it was, the review left no must-fix, no "
    "criterion changed, and no decision past the personas was taken without an answer"
)
SHORT = 7


def names(named: tuple[Named, ...]) -> str:
    """The reviewers by name."""
    return ", ".join(one.name for one in named)


def silent(named: Named) -> str:
    """A reviewer that gave no answer, and why."""
    return f"no answer from {named.name} ({named.why})"


def sub_of(review: Reviewed) -> str:
    """The line under a round: who answered, the silent, what ran and what was left out, and
    the commit it read."""
    answered = ", ".join(review.answered)
    parts = [f"answered: {answered}" if answered else "no source answered"]
    parts.extend(map(silent, review.silent))
    if review.ran:
        parts.append(f"ran {names(review.ran)}")
    if review.left_out:
        parts.append(f"left out {names(review.left_out)}")
    tip = review.tip[:SHORT]
    parts.append(f"on {tip}")
    return " · ".join(parts)


def round_row(world: World, review: Reviewed, at: int) -> Row:
    """The round `at` of the review, numbered from 0."""
    clean = rounds.verdict(review) == "clean"
    return Row(
        id=f"review-{at}",
        look="done" if clean else "bad",
        icon="check" if clean else "eye",
        head=rounds.line(review),
        subs=(sub_of(review),),
        time=stamp(review.at, world.clock.now, world.clock.zone),
    )


def rows(world: World, rounds: tuple[Reviewed, ...]) -> tuple[Row, ...]:
    """Each round of the review, in order."""
    numbered = enumerate(rounds)
    return tuple(round_row(world, one, at) for at, one in numbered)


def said_of(reviews: tuple[Reviewed, ...]) -> str | None:
    """The card's line: how many rounds, and a read of a conflict's resolution."""
    if not reviews:
        return None
    count = sum(1 for review in reviews if review.of != "resolution")
    parts = [plural(count, "round")]
    if any(review.of == "resolution" for review in reviews):
        parts.append("a read of a resolution")
    return " · ".join(parts)


def proposal(world: World, record: Record) -> Proposal | None:
    """The proposal: green with what green means, or not green with its reasons."""
    proposed = record.landing.proposed if record.landing else None
    if proposed is None:
        return None
    time = stamp(proposed.at, world.clock.now, world.clock.zone)
    if proposed.green:
        return Proposal(
            look="done", icon="check", said="Proposed: green", green=GREEN, time=time
        )
    count = len(proposed.reasons)
    said = f"Proposed: not green, for {plural(count, 'reason')}" if count else None
    listed = reasons(record, "pr", world.viewer.view, world.viewer.base)
    return Proposal(
        look="you",
        icon="triangle-exclamation",
        said=said or "Proposed: not green",
        reasons=listed,
        time=time,
    )
