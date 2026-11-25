"""`lem criteria change --typed` and `--unchanged`: the owner's No to the criteria that wait for
his yes, typed in the task's session, and a new wait of the same text when his note changes no
criterion (`criteria.cmd_typed` and `cmd_unchanged` on `main`).

His typed No is the answer to the wait that stands before the session writes a word of the new
text; an answer of the board that came first refuses it, and says which. After his No whose note
is a direction or a question, the same `criteria.md` waits for his yes again under a new
question, since his No refuses every yes to the one he answered.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.criteria import stopped, texts, where
from lem.app.decisions.writing import Change, written
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.criteria import change, digest, waits
from lem.records.base import Frozen
from lem.records.questions import Answer

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


class Answered(Frozen, frozen=True, kw_only=True):
    """The answer on record for the wait: the task, the question, whether this call wrote it,
    and the answer."""

    task: str
    question: str
    recorded: bool
    answer: Answer | None = None


class Again(Frozen, frozen=True, kw_only=True):
    """A new wait of the criteria: the task, his note, the new question, the file and the mark
    of its bytes that the page shows."""

    task: str
    words: str | None = None
    question: str
    path: str
    shown: str


def size_of(here: where.Here) -> str | None:
    """The size the task's `criteria.md` says, or None when there is none."""
    if not here.sheet.is_file():
        return None
    return texts.sheet_at(here.sheet, "the criteria").size


def answering(here: where.Here, words: str, record: Record) -> tuple[Change, Answered]:
    """His typed No, as the answer to the wait of `record`."""
    task = record.task
    refusal = change.changeable(task, "small" if size_of(here) == "small" else None)
    if refusal is not None:
        raise refusal
    after = change.typed(task, clock.now(), words)
    question = waits.question_of(after)
    if question is None:
        raise Refusal("not-waiting", "the criteria wait for nothing", "read the task")
    answered = Answered(
        task=here.slug,
        question=question.id,
        recorded=after is not task,
        answer=question.answer,
    )
    return lambda current: replace(current, task=after), answered


def typed(folder: Path, slug: str, words: str) -> Answered:
    """`lem criteria change SLUG --typed --words NOTE`."""
    note = " ".join(words.split())
    if not note:
        raise Refusal(
            "no-words",
            "--typed needs --words",
            "--words: his note, what the criteria say",
        )
    here = where.here_of(folder, slug)
    return written(here.workspace.state, slug, partial(answering, here, note))


def asking(here: where.Here, record: Record) -> tuple[Change, Again]:
    """The same criteria asked again, for the wait of `record`."""
    raw = texts.bytes_of(here.sheet, "the criteria that wait")
    stopped.unmoved(here, record, raw, here.sheet)
    said = waits.said_no(record.task)
    after = change.unchanged(record.task, clock.now(), digest.shown(raw))
    again = Again(
        task=here.slug,
        words=said.note if said else None,
        question=after.questions[-1].id,
        path=str(here.sheet),
        shown=digest.shown(raw),
    )
    return lambda current: replace(current, task=after), again


def unchanged(folder: Path, slug: str) -> Again:
    """`lem criteria change SLUG --unchanged`."""
    here = where.here_of(folder, slug)
    return written(here.workspace.state, slug, partial(asking, here))
