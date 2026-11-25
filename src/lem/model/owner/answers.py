"""The owner's answer to a question of a task, on the board or on a card (`answers.py` and
`board_model.answered_of` on `main`).

The first answer counts: a question answered once takes no second answer. An answer carries the
question's id and the digest of what he was shown, so an answer to an older question of the same
topic, or to a text that changed meanwhile, is refused. Once he answered on the board, the row
of that wait is the task's session's until the session took the answer into effect: the list
shows it no more.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.owner import answer_wait

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.holds import OwnerHold
    from lem.records.questions import Answer, Question
    from lem.records.task import Task


def taken_by_session(task: Task, topic: str, since: Moment) -> bool:
    """Whether the current question's answer waits for the task's session to take it."""
    asked = newest_of(task, topic)
    return (
        asked is not None
        and asked.asked >= since
        and asked.answer is not None
        and asked.took_effect is None
    )


def answered_hold(task: Task, hold: OwnerHold) -> bool:
    """Whether his answer to the question of the hold waits for the task's session."""
    topic = answer_wait.TOPICS.get(hold.on)
    return topic is not None and taken_by_session(task, topic, hold.since)


def answer(task: Task, question_id: str, digest: str | None, given: Answer) -> Task:
    """The task with his answer to the question `question_id`, shown with `digest`; refused
    for a question the task does not hold, one answered already, one a newer question of its
    topic replaced, a digest that is not the one the question shows, or an invalid option."""
    found = [one for one in task.questions if one.id == question_id]
    if not found:
        raise Refusal(
            "question",
            f"{task.slug} holds no question {question_id}",
            f"lem task show {task.slug} names the questions that wait",
        )
    asked = found[0]
    refusal = refused(task, asked, digest, given)
    if refusal is not None:
        raise refusal
    updated = replace(asked, answer=given)
    questions = tuple(
        updated if one.id == question_id else one for one in task.questions
    )
    return replace(task, questions=questions)


def refused(
    task: Task, asked: Question, digest: str | None, given: Answer
) -> Refusal | None:
    """Why an answer to `asked` may not count, or None."""
    why = why_refused(task, asked, digest)
    if why is not None:
        return Refusal("answered", why, "the owner reads the question as it is now")
    if not answer_wait.current(task, asked):
        return Refusal(
            "question",
            f"{asked.id} no longer waits for the owner",
            f"lem task show {task.slug} names the questions that wait",
        )
    option = given.option
    if option not in asked.options:
        choices = ", ".join(asked.options)
        return Refusal(
            "option",
            f"{option!r} is no option of {asked.id}",
            f"the owner chooses one of: {choices}",
        )
    needs_note = (asked.topic, option) in {("criterion", "no"), ("breaker", "help")}
    if needs_note and not (given.note and given.note.strip()):
        return Refusal("note", f"{option!r} needs a note", "add the owner's words")
    return None


def why_refused(task: Task, asked: Question, digest: str | None) -> str | None:
    """Why an answer may not count: answered already, asked again, or the text changed."""
    if asked.answer is not None:
        return f"{asked.id} was answered already: the first answer counts"
    newer = newer_of(task, asked)
    if newer is not None:
        return f"{asked.id} was asked again as {newer}"
    if asked.digest is None or digest == asked.digest:
        return None
    return f"the text of {asked.id} changed after the owner saw it"


def newer_of(task: Task, asked: Question) -> str | None:
    """The id of the question that replaced `asked`, or None. Cards are independent."""
    if asked.topic == "card":
        return None
    newest = newest_of(task, asked.topic)
    return newest.id if newest is not None and newest.id != asked.id else None


def newest_of(task: Task, topic: str) -> Question | None:
    """The last question of `topic` in record order, even when two share a moment."""
    matches = (one for one in reversed(task.questions) if one.topic == topic)
    return next(matches, None)
