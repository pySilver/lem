"""A change of the criteria from the owner's note, as its record and its page have it: the new
change of a task, a run again of one that stopped before its file, and what the page shows
(`criteria.cmd_change`, `change_of` and `cmd_pairs` on `main`)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.criteria import change, digest, waits
from lem.model.criteria.read import Sheet, sheet_of
from lem.records.base import Frozen
from lem.records.criteria import Change, Pair
from lem.records.criterion import Criterion

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.task import Task

ANSWERED = "the criteria.md the owner answered"
NAME = "criteria.md"


class Shown(Frozen, frozen=True, kw_only=True):
    """A change as the page shows it: his note, the question that waits, whether this call
    ended a change that stopped, the file and its mark, the criteria before and after, and the
    pairs."""

    task: str
    words: str
    question: str
    resumed: bool = False
    path: str
    shown: str
    before: tuple[Criterion, ...]
    after: tuple[Criterion, ...]
    pairs: tuple[Pair, ...]


def resumed(task: Task, shown: str) -> bool:
    """Whether the change on record asks his yes to the bytes of mark `shown`: a run again of
    the change, after it stopped before its file."""
    kept = task.criteria.change
    question = waits.question_of(task)
    if kept is None or question is None or question.asked != kept.at:
        return False
    return question.digest == shown


def made_of(
    answered: str, sides: tuple[Sheet, Sheet], words: str, now: datetime
) -> Change:
    """The change from the text he answered, with the marks of its two sides."""
    before, after = sides
    return Change(
        at=now,
        text=answered,
        words=words,
        before=digest.of_texts(before.size, before.criteria),
        after=digest.of_texts(after.size, after.criteria),
    )


def fresh(task: Task, texts: tuple[str, str], words: str, now: datetime) -> Task:
    """The task after a new change from the text he answered to the new text, the two of
    `texts`, by his note `words`."""
    answered, text = texts
    sides = (sheet_of(answered, ANSWERED), sheet_of(text, NAME))
    refusal = change.changeable(task, sides[0].size)
    if refusal is not None:
        raise refusal
    made = made_of(answered, sides, words, now)
    return change.changed(
        task, sides=sides, change=made, shown=digest.shown(text.encode())
    )


def shown_of(task: Task, path: str, text: str, *, again: bool) -> Shown:
    """The change on record of `task`, whose new text `text` is the file `path`."""
    made = task.criteria.change
    question = waits.question_of(task)
    if made is None or question is None:
        raise Refusal(
            "no-change",
            f"no change of {task.slug}'s criteria waits",
            f"lem criteria change {task.slug} --file FILE makes one",
        )
    return Shown(
        task=task.slug,
        words=made.words,
        question=question.id,
        resumed=again,
        path=path,
        shown=digest.shown(text.encode()),
        before=sheet_of(made.text, ANSWERED).criteria,
        after=sheet_of(text, NAME).criteria,
        pairs=made.pairs,
    )
