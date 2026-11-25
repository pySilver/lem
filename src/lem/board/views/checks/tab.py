"""The tab Checks and review of a task (`board_task.checks_tab` on `main`): the card of the
checks and the card of the review. A card of a task that ended with nothing in it is not drawn,
and a tab with neither says so; a pruned task says what went with its journal."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.inputs.task.checks import Checks
from lem.board.views.checks import commands, reviews
from lem.board.views.panel import pruned

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World

ENDED = frozenset(("landed", "answered", "dropped"))
NO_COMMAND = "The checks run when the branch’s turn to land comes"
NO_ROUND = "The review comes after the machine checks, before anything is proposed"
NEITHER = "The task ended with no checks and no review on record"


def checks(world: World, seen: Seen) -> Checks:
    """The tab Checks and review of the task `seen`."""
    if pruned.summary_of(seen) is not None:
        return Checks(went=pruned.went(world, seen, "checks"))
    ended = seen.record.task.status in ENDED
    card = gates(world, seen, ended=ended)
    review = reviewed(world, seen, ended=ended)
    empty = not (card.commands or card.ended_run or review.rounds or review.proposal)
    return replace(
        review,
        commands_said=card.commands_said,
        commands=card.commands,
        ended_run=card.ended_run,
        commands_empty=card.commands_empty,
        ended=NEITHER if ended and empty else None,
    )


def gates(world: World, seen: Seen, *, ended: bool) -> Checks:
    """The card of the checks: its commands, or the end of a run with none."""
    done = commands.listed(world, seen)
    ended_run = None if done else commands.ended_run(seen)
    landing = seen.record.landing
    return Checks(
        commands_said=commands.said_of(landing.checked if landing else None),
        commands=done,
        ended_run=ended_run,
        commands_empty=None if done or ended_run or ended else NO_COMMAND,
    )


def reviewed(world: World, seen: Seen, *, ended: bool) -> Checks:
    """The card of the review: its rounds and the proposal."""
    landing = seen.record.landing
    rounds = landing.reviews if landing else ()
    proposal = reviews.proposal(world, seen.record)
    rows = reviews.rows(world, rounds)
    return Checks(
        rounds_said=reviews.said_of(rounds),
        rounds=rows,
        proposal=proposal,
        rounds_empty=None if rows or proposal or ended else NO_ROUND,
    )
