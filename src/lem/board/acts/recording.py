"""His answer on the task's record, which the task's session takes as his typed word (`answers.
record` on `main`): Help, Drop, Build, the skip's Yes or No, and the criteria's No.

The question and the answer are one write with the act in the journal: the question the wait
asks goes on the record with it when the record held none, and the answer carries the option and
its label, his note, `board`, the listener, the device and the User-Agent whole, and the moment.
The board decides nothing more: the session acts on it, and sets when it took effect
(`model/owner/answers.py`).
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.decisions.writing import updated
from lem.board.acts import asking, checking, noting
from lem.kernel.errors import Refusal
from lem.model.owner import answers, turns
from lem.records.questions import Answer

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked
    from lem.records.questions import Question
    from lem.records.record import Record
    from lem.records.task import Task


def answer_of(option: str, asked: Asked) -> Answer:
    """His answer as the record keeps it."""
    asker = asked.asker
    return Answer(
        option=option,
        label=asking.label_of(option),
        note=asked.given.note or None,
        source="board",
        via=asker.via,
        device=asker.device,
        agent=asker.agent or None,
        at=asked.now,
    )


def with_question(task: Task, question: Question) -> Task:
    """The task with the question on record."""
    if not any(one.id == question.id for one in task.questions):
        return replace(task, questions=(*task.questions, question))
    questions = tuple(
        question if one.id == question.id else one for one in task.questions
    )
    return replace(task, questions=questions)


def answered(task: Task, question: Question, option: str, asked: Asked) -> Task:
    """The task with his answer to `question`, shown with the digest of the form when the
    question has one."""
    said = answer_of(option, asked)
    shown = None if question.digest is None else asked.given.digest
    return answers.answer(with_question(task, question), question.id, shown, said)


def answering(
    record: Record, *, asked: Asked, digest: str | None = None, act: str = "answer"
) -> Record:
    """The record with his answer to the question that waits, read again under the lock;
    `digest` is the mark of the criteria the page showed, given to a question of the
    criteria the record held none of."""
    question = checking.question_of(record.task, asked.given.key)
    option = checking.checked(question, asked.given)
    if question.topic == "criterion":
        question = criteria_question(record.task, question, digest)
    task = answered(record.task, question, option, asked)
    entry = noting.act_of(
        act, asked.asker, asked.now, question=question.id, option=option
    )
    return noting.with_act(replace(record, task=task), entry)


def criteria_question(task: Task, question: Question, digest: str | None) -> Question:
    """The criteria's question, once no read has the owner's turn."""
    if not turns.his_turn(task, alone=False):
        raise Refusal(
            "not-owner-turn",
            "The criteria do not wait for the owner. Nothing was recorded.",
            "read the task's page again after the persona read",
        )
    return replace(question, digest=digest) if question.digest is None else question


def recorded(asked: Asked, digest: str | None = None) -> Record:
    """Write his answer; refused when its question waits no more, or its option may not
    stand. `digest` is the mark of the criteria the page showed, for his No to them."""
    change = partial(answering, asked=asked, digest=digest)
    return updated(asked.state, asked.slug, change)
