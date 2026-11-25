"""The feed's words of the questions a task asked the owner that no move of its state says: a
card of its session, and whether to skip the personas' read of the criteria; and his answer to
a card (`card.asked`, `read.skip.asked` and `card.answered` of `main`'s `SAYS`). Each is told at
its own moment.

An answer the board took is an act of the owner in the journal, which says it: a card's answer is
told here only when no act of his names its question.
"""

from typing import TYPE_CHECKING

from lem.board.views.activity.tell_task import VIA
from lem.board.views.activity.told import CHECK, DONE, USER, YOU, Told
from lem.records.journal.task import OwnerAct

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.journal.entry import Entry
    from lem.records.questions import Answer, Question

CARD = "card"
SKIP = Told(
    YOU,
    "users",
    "Lem asked whether to skip the personas’ read",
    "the criteria name only you: your y or n",
)


def question(
    asked: Question, journal: tuple[Entry, ...]
) -> tuple[tuple[datetime, Told], ...]:
    """The question's ask, and his answer to a card that the board did not take."""
    if asked.topic == "skip":
        return ((asked.asked, SKIP),)
    if asked.topic != CARD:
        return ()
    card = Told(YOU, USER, "The task’s session asks you on a card", asked.question)
    found = asked.answer
    if found is None or acted_on(asked, journal):
        return ((asked.asked, card),)
    return (asked.asked, card), (found.at, answered(found))


def acted_on(asked: Question, journal: tuple[Entry, ...]) -> bool:
    """Whether an act of the owner in the journal names the question."""
    acts = (entry for entry in journal if isinstance(entry, OwnerAct))
    return any(entry.question == asked.id for entry in acts)


def answered(found: Answer) -> Told:
    """His answer to a card: on the board, from where and on what, or in the session."""
    if found.source != "board":
        return Told(DONE, CHECK, "You answered the card in the session")
    where = VIA.get(found.via or "", "")
    device = f", from the {found.device}" if found.device else ""
    return Told(DONE, CHECK, "You answered the card on the board", f"{where}{device}")
