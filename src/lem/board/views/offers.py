"""The acts the board offers on a task (`board_model.acts_of` on `main`): his yes while the
criteria wait for it and it would count, his merge while the pull request is open (not while Lem
lands it again after a moved base, while a merge of his stands, or while the forge calls it
conflicting), and his park while a breaker waits for him. A task two releases back is offered
none: its drop is the way on."""

from typing import TYPE_CHECKING

from lem.model.criteria import waits
from lem.model.landing import merge_standing
from lem.model.owner import merging
from lem.records.holds import BreakerHold, ReleaseHold

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.records.questions import Question
    from lem.records.task import Task

NONE: frozenset[str] = frozenset()


def open_question(task: Task, topic: str) -> Question | None:
    """The newest question of `topic` that the owner has not answered."""
    asked = (one for one in reversed(task.questions) if one.topic == topic)
    newest = next(asked, None)
    return newest if newest is not None and newest.answer is None else None


def approvable(task: Task) -> bool:
    """Whether his yes to the criteria is offered: their question stands, unanswered."""
    if isinstance(task.hold, ReleaseHold):
        return False
    asked = waits.question_of(task)
    return asked is not None and asked.answer is None


def merge_offered(seen: Seen, conflicts: frozenset[str] = NONE) -> bool:
    """Whether his merge is offered on the open pull request."""
    record = seen.record
    task = record.task
    if task.status != "open" or isinstance(task.hold, ReleaseHold):
        return False
    if merging.merge_wait(record) == "relands" or task.slug in conflicts:
        return False
    return merge_standing.standing_of(record) is None


def park_offered(task: Task) -> bool:
    """Whether his park is offered: a breaker waits for him."""
    return isinstance(task.hold, BreakerHold)
