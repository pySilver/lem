"""The acts the board offers on a task (`board_model.acts_of` on `main`): his yes while the
criteria wait for it and it would count, his merge while the pull request is open (not while Lem
lands it again after a moved base, while a merge of his stands, or while the forge calls it
conflicting), and his park while a breaker waits for him. A task two releases back is offered
none: its drop is the way on."""

from typing import TYPE_CHECKING

from lem.board.views.rule import ENDED
from lem.model.criteria import waits
from lem.model.landing import merge_standing
from lem.model.owner import answers, merging
from lem.records.holds import BreakerHold, OwnerHold, ReleaseHold

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.records.base import Moment
    from lem.records.questions import Question
    from lem.records.record import Record
    from lem.records.task import Task

NONE: frozenset[str] = frozenset()


def open_question(task: Task, topic: str) -> Question | None:
    """The newest unanswered question of the current hold."""
    since = held_since(task, topic)
    newest = answers.newest_of(task, topic)
    if since is None or newest is None or newest.asked < since:
        return None
    return newest if newest.answer is None else None


def held_since(task: Task, topic: str) -> Moment | None:
    """When the hold for this topic began, or None when it does not stand."""
    if task.status in ENDED:
        return None
    hold = task.hold
    if isinstance(hold, BreakerHold) and topic == "breaker":
        return hold.since
    if isinstance(hold, OwnerHold) and answers.TOPICS.get(hold.on) == topic:
        return hold.since
    return None


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
    if task.status != "open" or isinstance(task.hold, ReleaseHold):
        return False
    if (
        merge_pending(record)
        or merging.merge_wait(record) == "relands"
        or task.slug in conflicts
    ):
        return False
    return merge_standing.standing_of(record) is None


def park_offered(task: Task) -> bool:
    """Whether his park is offered: a breaker waits for him."""
    return task.status not in ENDED and isinstance(task.hold, BreakerHold)


def merge_pending(record: Record) -> bool:
    """Whether an open task has a merge call with no reply on record."""
    landing = record.landing
    return (
        record.task.status == "open"
        and landing is not None
        and landing.intent is not None
    )
