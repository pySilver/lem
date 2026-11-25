"""The owner's answer on record on a task's Overview (`board_task.answered_card` and
`answers.took_effect` on `main`): what he picked on the question of the task's hold, when and from
where, and his note, until the task's session takes it."""

from typing import TYPE_CHECKING

from lem.board.inputs.task.overview import Answered
from lem.board.views.panel.common import stamp
from lem.model.owner import answers
from lem.records.holds import BreakerHold, OwnerHold

# The place of a breaker's number in its question's id, `breaker:SLUG:N:MOMENT`.
NUMBER = 2

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.records.questions import Question
    from lem.records.task import Task


def answered(world: World, seen: Seen) -> Answered | None:
    """His answer that the task's session has not taken yet, or None."""
    asked = waiting(seen.record.task)
    made = asked.answer if asked else None
    if asked is None or made is None:
        return None
    if made.device:
        where = f", from the {made.device}"
    elif made.source == "session":
        where = ", in the task’s session"
    else:
        where = ""
    at = stamp(world, made.at)
    took = f"You picked {made.label} {what_of(asked)} at {at}{where}."
    return Answered(took=took, note=made.note)


def waiting(task: Task) -> Question | None:
    """The question of the task's hold whose answer waits for its session."""
    hold = task.hold
    if isinstance(hold, BreakerHold):
        topic = "breaker"
    elif isinstance(hold, OwnerHold):
        topic = answers.TOPICS.get(hold.on)
    else:
        return None
    if topic is None or not answers.taken_by_session(task, topic, hold.since):
        return None
    return answers.newest_of(task, topic)


def what_of(asked: Question) -> str:
    """What he answered: the plan, a breaker by its number, or the question's words."""
    if asked.topic == "plan":
        return "for the plan"
    if asked.topic == "breaker":
        parts = asked.id.split(":")
        number = parts[2] if len(parts) > NUMBER else ""
        return f"for breaker {number}".rstrip()
    return f"on “{asked.question}”"
