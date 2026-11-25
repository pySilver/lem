"""The owner's answer on record on a task's Overview (`board_task.answered_card` and
`answers.took_effect` on `main`): what he picked on the question of the task's hold, when and from
where, and his note, until the task's session takes it."""

from typing import TYPE_CHECKING

from lem.board.inputs.task.overview import Answered
from lem.board.views.offers import pending_answer
from lem.board.views.panel.common import stamp

# The place of a breaker's number in its question's id, `breaker:SLUG:N:MOMENT`.
NUMBER = 2

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.records.questions import Question


def answered(world: World, seen: Seen) -> Answered | None:
    """His answer that the task's session has not taken yet, or None."""
    asked = pending_answer(seen.record.task)
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


def what_of(asked: Question) -> str:
    """What he answered: the plan, a breaker by its number, or the question's words."""
    if asked.topic == "plan":
        return "for the plan"
    if asked.topic == "breaker":
        parts = asked.id.split(":")
        number = parts[2] if len(parts) > NUMBER else ""
        return f"for breaker {number}".rstrip()
    return f"on “{asked.question}”"
