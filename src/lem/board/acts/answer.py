"""`POST /HOST/WORKSPACE/tasks/SLUG/answer`: the owner's answer to a question of the board, from
its form: the question's id (`key`), the option, his note (`words`), the digest the page showed,
and Drop's confirm (`serve.act_answer` on `main`; `surfaces.md` B).

A breaker takes Help, Park or Drop; a plan Build or Drop; the skip of the persona read and the
criteria Yes or No. Park puts the task aside (`parking.py`), the criteria's Yes approves the
bytes the page showed (`approving.py`); every other answer goes on the record for the task's
session, which takes it as his typed word (`recording.py`). The server decides nothing more, and
wakes the session.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.board.acts import acting, approving, checking, parking, recording, telling
from lem.board.acts.asked import refused
from lem.board.acts.notes import Note
from lem.kernel.errors import Refusal
from lem.model.criteria import waits

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

    from lem.board.acts.asked import Asked
    from lem.records.questions import Question

ACT = "answer"
ON_RECORD = "Your answer is on record: the task’s session takes it."
# What the task's session does with each answer it takes from the board.
THEN = MappingProxyType(
    {
        "build": "it builds the plan",
        "drop": "it drops the task as on /lem drop",
        "help": "it takes your words to the lead as your part of the talk",
        "yes": "it takes your yes",
        "no": "it takes your no",
    }
)
CHANGES = "it changes the criteria from your words and asks for your yes again"


def told_of(asked: Asked, then: str) -> str:
    """The answer on record, and the word to the task's session."""
    told = telling.told(asked.checkout, asked.slug, asked.now, then)
    return f"{ON_RECORD} {told}"


def criteria_said(asked: Asked, question: Question, option: str) -> str:
    """His Yes or No to the criteria."""
    if option == "yes":
        return approving.approved(asked, question)
    recording.recorded(asked, approving.shown_of(asked))
    return told_of(asked, CHANGES)


def said_of(asked: Asked) -> str:
    """Take his answer, and say what came of it."""
    task = release.checked(asked.state, asked.slug).task
    question = checking.question_of(task, asked.given.key)
    option = checking.checked(question, asked.given)
    if option == "park":
        return parking.parked(asked, question)
    if question.topic == waits.TOPIC:
        return criteria_said(asked, question, option)
    recording.recorded(asked)
    return told_of(asked, THEN[option])


def answered(asked: Asked) -> Note:
    """The owner's answer, and its note."""
    try:
        said = said_of(asked)
    except Refusal as refusal:
        return refused(ACT, asked.slug, refusal)
    return Note(task=asked.slug, act=ACT, state="done", said=said)


async def endpoint(request: Request) -> Response:
    """The answer of the form, and the task's page with its note."""
    return await acting.on_task(request, answered)
