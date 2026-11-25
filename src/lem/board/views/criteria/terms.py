"""The words of the tab Criteria and decisions (`board_model.BY_WHOM`, `LADDER`, `TRACKS`,
`FAMILIES`, `IRREVERSIBLE`, `EXPERTS` and `board_task.CASE_WAS` on `main`): who took a decision,
the levels of the ladder, the tracks, how a case was had, and why a breaker stopped the build."""

from types import MappingProxyType

from lem.board.views.chips import BREAKS

BY_WHOM = MappingProxyType(
    {
        "lead": "the agent",
        "personas": "the personas",
        "owner": "you",
        "lem": "Lem",
        "experts": "the experts",
        "gate": "the question gate",
        "dialectic": "the dialectic",
    }
)
# The levels of the ladder, in the order a decision climbs them.
LADDER = (
    ("gate", "The question gate"),
    ("lead", "The agent"),
    ("personas", "The personas"),
    ("dialectic", "The dialectic"),
    ("experts", "The experts"),
)
# The levels past the personas: a decision one of them answered, or took, went past them.
PAST_PERSONAS = ("dialectic", "experts")
TRACKS = MappingProxyType({"small": "fast", "full": "standard"})
FAMILIES = MappingProxyType({1: "one model family", 2: "two model families"})
CASE_WAS = MappingProxyType(
    {
        "reproduced": "reproduced: a run showed it",
        "derived": "derived from the code, not run",
    }
)
EXPERTS = MappingProxyType({"fable": "Fable", "astra": "Astra"})
IRREVERSIBLE = MappingProxyType(
    {
        "data": "it destroys or rewrites data outside the worktree",
        "system": "it writes to a system outside the repository",
        "person": "it sends something to a person",
        "money": "it spends money",
    }
)


def track_words(size: str | None) -> str:
    """`standard track`, `fast track`, or `criteria` with no size."""
    return f"{TRACKS.get(size, size)} track" if size else "criteria"


def criteria_count(count: int) -> str:
    """`1 criterion`, `2 criteria`."""
    word = "criterion" if count == 1 else "criteria"
    return f"{count} {word}"


def stop_words(cause: str, kind: str | None) -> str:
    """Why a breaker stopped the build: its cause, and the kind of a step no “no” undoes."""
    said = BREAKS[cause]
    if cause == "irreversible" and kind:
        return f"{said}: {IRREVERSIBLE[kind]}"
    return said
