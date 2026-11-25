"""What a held task's card says while the step is not the owner's, or is a step of its own
(`board_model.settle`'s `WRITES_SAYS`, `SKIP_SAYS`, `GOES_ON`, `WORKS_SAYS` and the release stop
on `main`): the stage's line would say that it waits for him, which it does not now."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views import rule
from lem.records.holds import OwnerHold, ReleaseHold

if TYPE_CHECKING:
    from lem.records.record import Record

SKIP = "Lem asks whether to skip the personas' read of the criteria"
# What Lem does for a held task's step while the task runs without the owner.
GOES_ON = MappingProxyType(
    {
        "interview": (
            "Lem answers the interview with its own guesses, each in the task's decisions "
            "for the pull request, and approves the criteria without you"
        ),
        "criteria": (
            "Lem settles the criteria and approves them without you, each step in the "
            "task's decisions for the pull request"
        ),
        "request": (
            "Lem takes the safer read of the request and goes on without you, the read in "
            "the task's decisions for the pull request"
        ),
    }
)
# The line of each of Lem's turns under the owner's hold, by its label.
TURNS = MappingProxyType(
    {
        rule.WRITES.label: "Lem writes the criteria; then they come to you.",
        rule.READING.label: "nothing waits for you until their read is in",
        rule.WORKS.label: "it waits for you again when the session's turn ends",
    }
)


def said(record: Record, label: str) -> str | None:
    """The card's line of a held task in one of these steps, or None for any other."""
    hold = record.task.hold
    if isinstance(hold, ReleaseHold):
        return hold.say
    turn = TURNS.get(label)
    if turn is not None:
        return turn
    if not isinstance(hold, OwnerHold):
        return None
    if label == rule.GOES_ON.label:
        return GOES_ON.get(hold.on, GOES_ON["interview"])
    return SKIP if hold.on == "skip-read" else None
