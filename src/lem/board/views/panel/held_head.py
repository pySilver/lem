"""The head of the large card of a task the owner's hold or a breaker holds (`board_model.now_head`
on `main`, its `held` branch): his answer on record that its session has not taken yet, the
session that works on it, the breaker, a wait that goes on without him, the personas' read,
and each wait of his own."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.owner import answers, hold_question, turns
from lem.records.holds import BreakerHold

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.records.holds import OwnerHold
    from lem.records.task import Task

WAITS = "Waits for you"
CRITERIA_YES = "The criteria wait for your yes"
# The head of each wait of his own that its kind says alone.
OWN = MappingProxyType(
    {
        "skip-read": "Lem asks you whether to skip the personas’ read",
        "criteria": CRITERIA_YES,
        "plan": "The plan waits for you",
    }
)


def held(seen: Seen, *, alone: bool = False) -> str:
    """What a held task does now; `alone` while it runs without the owner."""
    task, session = seen.record.task, seen.session
    if isinstance(task.hold, BreakerHold):
        return breaker(task, working=bool(session and session.working))
    if session is not None and session.live and session.working:
        return "Its session works on your answer"
    return owner_held(task, alone=alone)


def owner_held(task: Task, *, alone: bool) -> str:
    """A wait of the owner: his answer on record, a wait that goes on without him, or his
    step."""
    hold = turns.held(task)
    if hold is None:
        return WAITS
    if answers.answered_hold(task, hold):
        return "Approved: its lead has not started yet"
    if alone and hold.on in turns.GOES_ON:
        return "Lem goes on without you"
    return waiting(task, hold)


def breaker(task: Task, *, working: bool) -> str:
    """A breaker: his help on record, the session that works on it, or the breaker that
    waits."""
    if hold_question.pending_answer(task) is not None:
        return "Helped: its lead has not started yet"
    if working:
        return "Its session works on your answer"
    return "The build stopped: its breaker waits for you"


def waiting(task: Task, hold: OwnerHold) -> str:
    """A wait of his: the personas' read, the interview and the criteria it ends in, or his
    own step."""
    if turns.reading(task, hold.since):
        return "The personas read the criteria"
    if hold.on != "interview":
        return OWN.get(hold.on, WAITS)
    if turns.asked(task) is None:
        return "The interview waits for you"
    return (
        CRITERIA_YES
        if turns.interview_turn(task, hold.since)
        else "Lem writes the criteria"
    )
