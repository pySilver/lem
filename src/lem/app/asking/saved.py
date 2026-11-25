"""The card's immutable page and the question by which the task knows it."""

from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from lem.app.asking import keys, updates
from lem.app.asking.shape import Card
from lem.kernel import clock, errors, files
from lem.records.journal.task import OwnerAct
from lem.records.questions import Question
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

PAGE = "page.html"
FORM = "card.json"


def keep(folder: Path, card: Card, body: bytes) -> None:
    """Publish the page before the task cites it."""
    path = keys.copies(folder, card.page)
    digest = files.publish(path / PAGE, body)
    files.publish(path / FORM, msgspec.json.encode(card))
    asked = Question(
        id=keys.question_id(card.page),
        topic="card",
        question=card.prompts[0].prompt,
        options=("answered", "closed", "dismissed"),
        digest=digest,
        asked=clock.now(),
    )
    updates.changed(folder, lambda record: added(record, asked))


def added(record: Record, asked: Question) -> Record:
    """The task with the card it asks and the journal line for it."""
    if named(record, asked.id) is not None:
        raise errors.Refusal(
            "ask-page", f"the task already has {asked.id}", "ask with a new page"
        )
    task = replace(record.task, questions=(*record.task.questions, asked))
    act = OwnerAct(at=asked.asked, act="card.asked", question=asked.id)
    return replace(record, task=task, journal=(*record.journal, act))


def named(record: Record, key: str) -> Question | None:
    """The card the task keeps under this question id."""
    cards = (one for one in record.task.questions if one.topic == "card")
    return next((one for one in cards if one.id == key), None)


def question(folder: Path, page: str) -> Question | None:
    """The task's question for this page, if it exists."""
    record = tasks.read(folder.parents[1], folder.name)
    return named(record, keys.question_id(page))


def metadata(folder: Path, page: str) -> Card:
    """What the page asks, for the board's answer and the opening session."""
    path = keys.copies(folder, page) / FORM
    try:
        return msgspec.json.decode(path.read_bytes(), type=Card)
    except (OSError, msgspec.DecodeError) as error:
        raise errors.Fault(f"the board cannot read card {page}: {error}") from error


def html(folder: Path, page: str, digest: str | None) -> bytes:
    """The page on record with the digest the owner is about to see."""
    body = (keys.copies(folder, page) / PAGE).read_bytes()
    if files.digest(body) != digest:
        raise errors.Fault(f"the page of card {page} differs from the task's record")
    return body
