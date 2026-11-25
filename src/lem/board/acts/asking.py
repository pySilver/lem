"""The question a task's wait asks the owner on the board, and its id (`answers.key_of` and
`board_model.answer_row` on `main`).

Four waits take an answer on the board: a breaker (Help, Park or Drop), a plan that waits for his
read (Build or Drop), "Skip the persona read?" (Yes or No), and the criteria that wait for his yes
(Yes or No). The question is the record's own when the task holds one, asked since the wait
began; else the one the wait asks, with an id from the wait: `breaker:SLUG:N:STAMP`,
`plan:SLUG:STAMP`, `skip:SLUG:STAMP`, `criterion:SLUG:STAMP`, STAMP the moment the wait began
(`clock.compact`). A wait that begins again is a new id, so an answer applies to the wait it
answered and no later one. The page's form names this id (`key`), and the act writes the
question on the record with his answer, when it was not there.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.kernel import clock
from lem.model.criteria import waits
from lem.records.holds import BreakerHold, OwnerHold
from lem.records.questions import Question, Topic

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.task import Task

# Each topic's options, in the order the buttons show them.
OPTIONS = MappingProxyType(
    {
        "breaker": ("help", "park", "drop"),
        "plan": ("build", "drop"),
        "skip": ("yes", "no"),
        "criterion": ("yes", "no"),
    }
)
SKIP = "Skip the persona read?"
# A wait the board answers: its topic, when it began, and its question's words.
type Wait = tuple[Topic, Moment, str]


def derived(topic: Topic, task: Task, since: Moment, words: str) -> Question:
    """The question of a wait the record holds none of, asked when the wait began."""
    hold = task.hold
    middle = f":{hold.number}" if isinstance(hold, BreakerHold) else ""
    stamp = clock.compact(since)
    return Question(
        id=f"{topic}:{task.slug}{middle}:{stamp}",
        topic=topic,
        question=words,
        options=OPTIONS[topic],
        asked=since,
    )


def recorded(task: Task, topic: str, since: Moment) -> Question | None:
    """The record's newest question of `topic`, when it was asked since the wait began."""
    found = (one for one in reversed(task.questions) if one.topic == topic)
    newest = next(found, None)
    return newest if newest is not None and newest.asked >= since else None


def wait_of(task: Task) -> Wait | None:
    """The topic, the start and the words of the wait the board answers, or None."""
    hold = task.hold
    if isinstance(hold, BreakerHold):
        words = f"Breaker {hold.number} of {task.slug}: help, park or drop the task?"
        return "breaker", hold.since, words
    if not isinstance(hold, OwnerHold):
        return None
    return owner_wait(task, hold)


def owner_wait(task: Task, hold: OwnerHold) -> Wait | None:
    """The topic, the start and the words of the owner's wait the board answers, or None."""
    if hold.on == "plan" and task.status == "planned":
        return "plan", hold.since, f"Build the plan of {task.slug}, or drop the task?"
    if hold.on == "skip-read":
        return "skip", hold.since, SKIP
    if hold.on in waits.WAITING:
        return waits.TOPIC, hold.since, waits.QUESTION
    return None


def standing(task: Task) -> Question | None:
    """The question the board answers now for the task: the record's, or the wait's own."""
    wait = wait_of(task)
    if wait is None:
        return None
    topic, since, words = wait
    return recorded(task, topic, since) or derived(topic, task, since, words)


def label_of(option: str) -> str:
    """The label of an option, as its button says it."""
    return option.capitalize()


def on_record(task: Task, question: Question) -> bool:
    """Whether the task holds the question."""
    return any(one.id == question.id for one in task.questions)
