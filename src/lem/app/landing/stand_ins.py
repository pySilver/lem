"""The pull request's account of the seats that stood in and any that failed too."""

from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
        "usage-limit": "reached its usage limit",
        "model": "did not know the model",
    }
)


def agent_of(seat: str) -> str:
    """The seat's agent, by its name in the pull request."""
    agent = seat.partition("/")[0].partition(":")[0]
    return AGENTS.get(agent, agent)


def why(seat: str, error: SeatError) -> str:
    """The agent's name and the failure that kept it from its seat."""
    named, failed = agent_of(seat), ERRORS[error]
    return f"{named} {failed}"


def failed_too(stood: StandIn, later: tuple[StandIn, ...]) -> SeatError | None:
    """The stand-in's own failure before the owner's go on."""
    if stood.failed_too is not None:
        return stood.failed_too.error
    return next(
        (
            one.error
            for one in later
            if one.seat == stood.seat
            and one.again == stood.again
            and one.failed == stood.took
            and one.took is None
        ),
        None,
    )


type History = tuple[StandIn, ...]


def shown(stood: StandIn, took: str, later: History) -> tuple[str, str]:
    """The line of a stand-in, and the line that takes its place when it fails."""
    role = SEATS[stood.seat]
    first = why(stood.failed, stood.error)
    who = f"`{took}` in place of `{stood.failed}`: {first}"
    plain = f"- {role} was {who}"
    error = failed_too(stood, later)
    if error is None:
        return plain, plain
    return plain, failed_line(f"- {role} was to be {who}", took, error)


def failed_line(prefix: str, took: str, error: SeatError) -> str:
    """What the pull request says when the stand-in also fails."""
    agent, second = agent_of(took), why(took, error)
    return f"{prefix}; then {agent} gave an error too: {second}"


# A stand-in's line while it holds, and the line that takes its place.
type Line = tuple[str, str]


def lines(history: History, role: str | None = None) -> tuple[Line, ...]:
    """Each stand-in of `role` (of every role for None), in task order, as its line and its
    final form: two stand-ins of the same seats are two, so that one that failed and a later
    one that read are both told, and the same stand-in kept twice is one."""
    written: list[Line] = []
    for index, stood in enumerate(history):
        if stood.took is None or role not in {None, stood.seat}:
            continue
        edit = shown(stood, stood.took, history[index + 1 :])
        if edit not in written:
            written.append(edit)
    return tuple(written)


def finals(history: History, role: str | None = None) -> tuple[str, ...]:
    """The final line of each stand-in, in task order, each text once."""
    told = (final for _, final in lines(history, role))
    return tuple(dict.fromkeys(told))
