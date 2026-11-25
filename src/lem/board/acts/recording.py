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

from lem.board.acts import asking, checking, noting
from lem.model.owner import answers
from lem.records.questions import Answer

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked
    from lem.records.questions import Question
    from lem.records.record import Record
    from lem.records.task import Task


def answer_of(question: Question, option: str, asked: Asked) -> Answer:
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
    if asking.on_record(task, question):
        return task
    return replace(task, questions=(*task.questions, question))


def answered(task: Task, question: Question, option: str, asked: Asked) -> Task:
    """The task with his answer to `question`, shown with the digest of the form when the
    question has one."""
    said = answer_of(question, option, asked)
    shown = None if question.digest is None else asked.given.digest
    return answers.answer(with_question(task, question), question.id, shown, said)


def answering(record: Record, *, asked: Asked, digest: str | None) -> Record:
    """The record with his answer to the question that waits, read again under the lock;
    `digest` is the mark of the criteria the page showed, given to a question of the
    criteria the record held none of."""
    question = checking.question_of(record.task, asked.given.key)
    option = checking.checked(question, asked.given)
    if question.topic == "criterion" and question.digest is None:
        question = replace(question, digest=digest)
    task = answered(record.task, question, option, asked)
    entry = noting.act_of(
        "answer", asked.asker, asked.now, question=question.id, option=option
    )
    return noting.with_act(replace(record, task=task), entry)


def recorded(asked: Asked, digest: str | None = None) -> Record:
    """Write his answer; refused when its question waits no more, or its option may not
    stand. `digest` is the mark of the criteria the page showed, for his No to them."""
    change = partial(answering, asked=asked, digest=digest)
    return noting.written(asked.state, asked.slug, change)
