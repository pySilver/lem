"""The question of an owner's hold that the board answers, and its renewal on Resume."""

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from msgspec.structs import replace

from lem.kernel import clock
from lem.model.task import question_keys
from lem.records.questions import Question

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.records.base import Moment
    from lem.records.holds import OwnerHold, OwnerWait
    from lem.records.questions import Topic
    from lem.records.task import Task

CRITERIA = "Approve the criteria?"
SKIP = "Skip the persona read?"
PLAN: Final = "plan"
TOPICS: Mapping[OwnerWait, Topic] = MappingProxyType(
    {
        "interview": "criterion",
        "criteria": "criterion",
        "skip-read": "skip",
        PLAN: PLAN,
    }
)
OPTIONS = MappingProxyType(
    {PLAN: ("build", "drop"), "skip": ("yes", "no"), "criterion": ("yes", "no")}
)


def words_of(topic: Topic, slug: str) -> str:
    """The words of a board question for the owner's wait."""
    if topic == PLAN:
        return f"Build the plan of {slug}, or drop the task?"
    return SKIP if topic == "skip" else CRITERIA


def key_of(topic: Topic, slug: str, since: Moment) -> str:
    """The key shared by the questions of one owner hold."""
    stamp = clock.compact(since)
    return f"{topic}:{slug}:{stamp}"


def asked(task: Task, hold: OwnerHold) -> Question | None:
    """The first question of the exact hold; some owner holds take no board answer."""
    topic = TOPICS.get(hold.on)
    if topic is None or (topic == PLAN and task.status != "planned"):
        return None
    return Question(
        id=key_of(topic, task.slug, hold.since),
        topic=topic,
        question=words_of(topic, task.slug),
        options=OPTIONS[topic],
        asked=hold.since,
    )


def current(task: Task, hold: OwnerHold) -> Question | None:
    """The board's question of this exact hold, if it takes a board answer."""
    first = asked(task, hold)
    return None if first is None else question_keys.recorded(task, first.id) or first


def renewed(task: Task, hold: OwnerHold) -> Task:
    """Renew the form for the same owner hold, keeping the original prompt and digest."""
    before = current(task, hold)
    if before is None:
        return replace(task, hold=hold)
    key = question_keys.fresh(task, question_keys.base_of(before.id))
    question = replace(before, id=key, answer=None, took_effect=None)
    return replace(task, hold=hold, questions=(*task.questions, question))
