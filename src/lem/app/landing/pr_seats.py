"""The pull request's account of each seat that stood in and its own failure, if any."""

from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines
    from lem.records.work import SeatError, StandIn

SEATS = MappingProxyType(
    {"reviewer": "the reviewer", "planner": "the planner", "merger": "the merge agent"}
)
AGENTS = MappingProxyType({"claude": "Claude Code", "codex": "Codex"})
ERRORS = MappingProxyType(
    {
        "missing": "is not on this Mac",
        "login": "had no login",
        "tokens": "had no tokens",
        "model": "did not know the model",
    }
)


def agent_of(seat: str) -> str:
    """The agent's name without its model and effort."""
    agent = seat.partition("/")[0].partition(":")[0]
    return AGENTS.get(agent, agent)


def failure(found: StandIn, after: tuple[StandIn, ...]) -> SeatError | None:
    """The same fallback's error before the owner tried the seat again."""
    if found.failed_too is not None:
        return found.failed_too.error
    same_attempt = (
        later
        for later in after
        if later.seat == found.seat and later.again == found.again
    )
    return next(
        (
            later.error
            for later in same_attempt
            if later.failed == found.took and later.took is None
        ),
        None,
    )


def line(found: StandIn, took: str, error: SeatError | None) -> str:
    """One line for the stand-in, including the reason its own start failed."""
    seat, agent = SEATS[found.seat], agent_of(found.failed)
    cause = ERRORS[found.error]
    if error is None:
        return f"- {seat} was `{took}` in place of `{found.failed}`: {agent} {cause}"
    fallback = agent_of(took)
    ending = ERRORS[error]
    return (
        f"- {seat} was to be `{took}` in place of `{found.failed}`: {agent} {cause}; "
        f"then {fallback} gave an error too: {fallback} {ending}"
    )


def lines(found: tuple[StandIn, ...]) -> Lines:
    """Each stand-in, with a second failure on its own line of account."""
    return tuple(
        line(one, one.took, failure(one, found[index + 1 :]))
        for index, one in enumerate(found)
        if one.took is not None
    )
