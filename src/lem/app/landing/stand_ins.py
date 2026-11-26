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


def lines(history: History, role: str | None = None) -> dict[str, str]:
    """Each distinct stand-in line and its final form, in task order."""
    written: dict[str, str] = {}
    for index, stood in enumerate(history):
        if stood.took is None or role not in {None, stood.seat}:
            continue
        later = history[index + 1 :]
        edit = shown(stood, stood.took, later)
        if edit[0] == edit[1]:
            written.setdefault(*edit)
        else:
            written[edit[0]] = edit[1]
    return written
