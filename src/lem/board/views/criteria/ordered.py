"""The decisions and breakers of the build on their card (`board_task.decision_rows` and
`board_model.decisions_sum` on `main`): the breaker that waits first, then the important
decisions, then every other one with the breakers that no longer wait, each group in the
record's order; and the owner's help that names a breaker the record does not hold."""

from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.names import plural
from lem.board.inputs.parts import Row
from lem.board.views.criteria.breakers import breaker_of
from lem.board.views.criteria.decided import decision_of
from lem.board.views.criteria.says import importance
from lem.records.decisions import Breaker, Taken
from lem.records.holds import BreakerHold

if TYPE_CHECKING:
    from lem.board.inputs.task.decisions import Decision
    from lem.board.views.world import Seen, World

type Shown = Taken | Breaker


def first(seen: Seen, one: Shown) -> int:
    """A decision's group: the breaker that holds the task, an important decision, any
    other."""
    hold = seen.record.task.hold
    if isinstance(one, Breaker):
        held = isinstance(hold, BreakerHold) and hold.number == one.id
        return 0 if held else 2
    return 1 if importance(seen.record, one) else 2


def decisions(world: World, seen: Seen) -> tuple[Decision, ...]:
    """Each decision and breaker, in the card's order."""
    shown = [
        one for one in seen.record.task.decisions if isinstance(one, (Taken, Breaker))
    ]
    ordered = sorted(shown, key=lambda one: first(seen, one))
    return tuple(
        breaker_of(world, seen, one)
        if isinstance(one, Breaker)
        else decision_of(world, seen, one)
        for one in ordered
    )


def orphans(world: World, seen: Seen) -> tuple[Row, ...]:
    """Each help of the owner's that names a breaker the record does not hold."""
    every = seen.record.task.decisions
    breakers = {one.id for one in every if isinstance(one, Breaker)}
    helps = (
        one
        for one in every
        if isinstance(one, Taken)
        and one.breaker is not None
        and one.breaker not in breakers
    )
    return tuple(orphan(world, one) for one in helps)


def orphan(world: World, help_: Taken) -> Row:
    """A help that names a breaker that is not in the log."""
    moment = help_.at.strftime("%Y%m%dT%H%M%SZ")
    return Row(
        id=f"orphan-{help_.id}-{moment}",
        look="bad",
        icon="triangle-exclamation",
        head=(
            f"Your help, decision {help_.id}, names breaker {help_.breaker}, which is not "
            "in the log"
        ),
        text=f": {help_.chose}",
        time=stamp(help_.at, world.clock.now, world.clock.zone),
    )


def said_of(seen: Seen) -> str | None:
    """The card's line: how many decisions were taken, how many are important, the
    breakers."""
    record = seen.record
    taken = [one for one in record.task.decisions if isinstance(one, Taken)]
    breakers = sum(1 for one in record.task.decisions if isinstance(one, Breaker))
    important = sum(1 for one in taken if importance(record, one))
    parts = (
        f"{len(taken)} taken" if taken else "",
        f"{important} important" if important else "",
        plural(breakers, "breaker") if breakers else "",
    )
    return " · ".join(part for part in parts if part) or None
