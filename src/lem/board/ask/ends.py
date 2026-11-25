"""The first end of a card, as the task's question and its saved payload."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.ask import keys, receipts, saved, updates
from lem.kernel.errors import Refusal
from lem.model.owner import answers
from lem.records.journal import task as journal_entry

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records import questions
    from lem.records.record import Record

type Payload = receipts.Payload


def time_of_answer() -> datetime:
    """The exact time names the immutable artifact of this attempt."""
    return datetime.now(UTC)


def finish(
    folder: Path, asked: questions.Question, answer: questions.Answer, payload: Payload
) -> tuple[bool, questions.Answer]:
    """Publish the attempted answer, then let the task's first answer count."""
    page = asked.id.removeprefix("card:")
    actual = receipts.kept(keys.copies(folder, page), answer.at, payload)
    proposal = replace(answer, at=actual)
    try:
        updates.changed(folder, lambda record: applied(record, asked, proposal))
    except Refusal as refused:
        return False, winner(folder, page, refused)
    return True, proposal


def winner(folder: Path, page: str, refused: Refusal) -> questions.Answer:
    """The first answer after a lost race, or the refusal that still holds."""
    fresh = saved.question(folder, page)
    if fresh is None or fresh.answer is None:
        raise refused
    return fresh.answer


def applied(
    record: Record, asked: questions.Question, answer: questions.Answer
) -> Record:
    """Commit one end and its journal line in the same write."""
    task = answers.answer(record.task, asked.id, asked.digest, answer)
    act = journal(asked.id, answer)
    return replace(record, task=task, journal=(*record.journal, act))


def journal(key: str, answer: questions.Answer) -> journal_entry.OwnerAct:
    """A card's answer or close in the task's journal."""
    act = "card.answered" if answer.option == "answered" else "card.closed"
    return journal_entry.OwnerAct(
        at=answer.at,
        act=act,
        question=key,
        option=answer.option,
        via=answer.via or "session",
    )


def description(answer: questions.Answer) -> str:
    """What took effect and where the owner answered."""
    where = "on the board" if answer.source == "board" else "in the session"
    device = f" from the {answer.device}" if answer.device else ""
    at = answer.at.astimezone().strftime("%H:%M")
    if answer.option != "answered":
        return f"The card was {answer.option} {where} at {at}."
    return f"{answer.label} was recorded {where} at {at}{device}."
