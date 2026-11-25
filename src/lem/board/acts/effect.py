"""What the board says when an answer finds its question answered or gone: the answer that took
effect, or what holds the task now (`answers.took_effect` and `serve.row_refusal` on `main`).

"You picked Drop for breaker 1 at 15:40, from the phone": the first answer counts, and the second
is told which one did. An answer from a page that showed an earlier wait, or one whose wait
ended, records nothing and says what holds now.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.acts.asking import label_of
from lem.kernel.errors import Refusal
from lem.records.holds import Parked

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.questions import Answer, Question
    from lem.records.task import Task

NOTHING = "Nothing was recorded."
# What an answer was for, where the question's own words would say too much.
WHATS = MappingProxyType({"plan": "for the plan", "breaker": "for the breaker"})


def hhmm(moment: datetime) -> str:
    """The moment as a clock on this Mac shows it."""
    return moment.astimezone().strftime("%H:%M")


def where(answer: Answer) -> str:
    """Where the answer was given: the device, the task's session, or nothing."""
    if answer.device is not None:
        return f", from the {answer.device}"
    if answer.source == "session":
        return ", in the task’s session"
    return ""


def took_effect(question: Question, answer: Answer) -> str:
    """The answer on record, in one sentence."""
    label = label_of(answer.option)
    what = WHATS.get(question.topic) or f"on “{question.question}”"
    clock = hhmm(answer.at)
    place = where(answer)
    return f"You picked {label} {what} at {clock}{place}"


def answered(question: Question, answer: Answer) -> Refusal:
    """The refusal of a second answer: the first one counts."""
    return Refusal(
        "answered",
        f"{took_effect(question, answer)}: the first answer counts. {NOTHING}",
        "the task’s session takes the answer on record",
    )


def gone(task: Task, standing: Question | None, topic: str | None) -> Refusal:
    """The refusal of an answer whose question waits no more: what holds the task now."""
    if standing is not None and standing.topic == topic:
        since = hhmm(standing.asked)
        why = (
            f"“{standing.question}” waits again since {since}, and the page you answered "
            f"from showed an earlier wait. {NOTHING}"
        )
        return Refusal("asked-again", why, "read it again, then answer")
    held = task.hold
    now = f"it is {task.status} since {hhmm(task.since)}"
    if isinstance(held, Parked):
        now = f"you parked it at {hhmm(held.since)}"
    why = f"That question of {task.slug} no longer waits: {now}. {NOTHING}"
    return Refusal("not-waiting", why, "read the task's page again")
