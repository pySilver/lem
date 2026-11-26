"""The acts the board offers on a task (`board_model.acts_of` on `main`): his yes while the
criteria wait for it and it would count, his merge while the pull request is open (not while Lem
lands it again after a moved base, while a merge of his stands, or while the forge calls it
conflicting), and his park while a breaker waits for him. A task two releases back is offered
none: its drop is the way on."""

from typing import TYPE_CHECKING

from lem.board.views import merge_state
from lem.board.views.rule import ENDED
from lem.model.criteria import waits
from lem.model.landing import merge_standing
from lem.model.owner import hold_question, merging
from lem.records.holds import BreakerHold, OwnerHold, Parked, ReleaseHold

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.records.questions import Question
    from lem.records.task import Task

NONE: frozenset[str] = frozenset()


def active_question(task: Task) -> Question | None:
    """The question of the active hold, if the board can answer it."""
    if task.status in ENDED:
        return None
    hold = task.hold
    if isinstance(hold, OwnerHold) and hold.on in waits.WAITING:
        return waits.question_of(task)
    return hold_question.standing(task)


def open_question(task: Task, topic: str) -> Question | None:
    """The unanswered question of the active hold, if its topic agrees."""
    asked = active_question(task)
    if asked is None or asked.topic != topic or asked.answer is not None:
        return None
    return asked


def pending_answer(task: Task) -> Question | None:
    """An answer to this hold which its session has yet to take."""
    asked = active_question(task)
    if asked is None or asked.answer is None or asked.took_effect is not None:
        return None
    return asked


def skip_held(task: Task) -> bool:
    """Whether the task waits for the owner to answer the skip question."""
    hold = task.hold
    return (
        task.status not in ENDED
        and isinstance(hold, OwnerHold)
        and hold.on == "skip-read"
    )


def approvable(task: Task) -> bool:
    """Whether his yes to the criteria is offered: their question stands, unanswered."""
    if task.status in ENDED or isinstance(task.hold, ReleaseHold):
        return False
    asked = waits.question_of(task)
    return asked is not None and asked.answer is None


def merge_offered(seen: Seen, conflicts: frozenset[str] = NONE) -> bool:
    """Whether his merge is offered on the open pull request."""
    record = seen.record
    task = record.task
    if task.status != "open" or isinstance(task.hold, Parked | ReleaseHold):
        return False
    if (
        merge_state.current(record) is not None
        or merge_state.proposal_refusal(seen) is not None
        or merging.merge_wait(seen.merge_look()) == "relands"
        or task.slug in conflicts
    ):
        return False
    return merge_standing.standing_of(record) is None


def park_offered(task: Task) -> bool:
    """Whether his park is offered: a breaker waits for him."""
    return task.status not in ENDED and isinstance(task.hold, BreakerHold)
