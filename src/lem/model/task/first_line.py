"""The first line of a task to the owner, composed by Lem from the task's record, which its
session says as it is (the owner's rulings "The first line of a task is composed by Lem, and its
session says it as it is" and "The first line is where he corrects Lem's read of a request").

It says the type with his words, the branch, the track with its steps, what waits for him, and
the commands that correct the read (`opening_line_facts` and `compose_opening_line` on `main`).
In three of four real tasks on 2026-11-21 (lem-trial and lem-scratch) a session told to say the
line in a form the stage gave said "The builder runs now" instead, so Lem composes it.

The quote is the fast track's first criterion, else the outcome of `task.md`, else the backlog
item's title, else his ask, without the `/lem` that carried it.
"""

import re

from lem.model.task import first_steps, first_words, quotes
from lem.model.task.outcome import outcome_of
from lem.records.base import Frozen
from lem.records.holds import OwnerHold
from lem.records.task import Shape, Task, Then

LEM = re.compile(r"^/lem\s+")


class Read(Frozen, frozen=True, kw_only=True):
    """What the line reads beside the record: `criteria.md` and `task.md` of the task's
    folder, the backlog item's title, and whether the investigation's report is there."""

    criteria: str = ""
    outcome: str = ""
    title: str | None = None
    report: bool = False


class Line(Frozen, frozen=True, kw_only=True):
    """What a first line is made of: the task, its shape, the words it quotes, and what says
    what is wanted in place of an interview."""

    task: Task
    shape: Shape
    then: Then
    quote: str | None = None
    stands_in: str


def quote_of(task: Task, then: Then, read: Read) -> str | None:
    """The words the line quotes, as the middle of a line."""
    quote = quotes.criterion_of(read.criteria) if then == "fast" else None
    quote = quote or outcome_of(read.outcome) or read.title
    words = LEM.sub("", " ".join(task.ask.split()))
    if not quote and words:
        quote = quotes.first_sentence(words)
    return quotes.in_his_words(quote) if quote else None


def stands_in(task: Task, read: Read) -> str:
    """What says what is wanted, for a request that goes to the lead with no interview."""
    if task.ticket is not None:
        return "the ticket"
    if task.backlog_item is not None:
        return "the backlog item"
    return "the investigation's report" if read.report else "your request"


def line_of(task: Task, read: Read) -> Line | None:
    """What the task's first line is made of; None for a night task, whose report names it,
    before its read names its path, and while his order waits for his answer."""
    shape = task.shape
    hold = task.hold
    if task.night is not None or shape is None or shape.then is None:
        return None
    if isinstance(hold, OwnerHold) and hold.on == "order":
        return None
    return Line(
        task=task,
        shape=shape,
        then=shape.then,
        quote=quote_of(task, shape.then, read),
        stands_in=stands_in(task, read),
    )


def composed(line: Line, named: str | None) -> str:
    """The first line itself. With `named`, the line as another session says it: the task
    named first, and its name in each command."""
    words = (
        *first_words.head(line, named),
        *first_words.waits(line, named),
        *first_steps.steps(line, named),
    )
    return " ".join(word for word in words if word)
