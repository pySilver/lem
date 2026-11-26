"""Renew a breaker's question after the owner's Help ends without a decision."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.decisions import book
from lem.model.task import breaker_question
from lem.records.holds import BreakerHold
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.record import Record


def renewed(record: Record, *, key: str, line: str, now: Moment) -> Record:
    """Keep the breaker and its answered question, and renew its wait under a new key."""
    task = record.task
    book.writable(task)
    hold = task.hold
    if not isinstance(hold, BreakerHold):
        raise Refusal(
            "no-breaker",
            f"no breaker of {task.slug} waits for the owner",
            f"lem decisions pending {task.slug} names its breakers",
        )
    question = breaker_question.current(task, hold)
    answer = question.answer
    if (
        question.id != key
        or not answer
        or (answer.source, answer.option) != ("board", "help")
    ):
        raise Refusal(
            "breaker-question",
            f"{key} is not the current Help answer of breaker {hold.number}",
            f"lem task show {task.slug} names the answer to the current hold",
        )
    task = breaker_question.renewed(task, hold, now)
    noted = StateNoted(at=now, status=task.status, hold="breaker", line=line)
    return replace(record, task=task, journal=(*record.journal, noted))
