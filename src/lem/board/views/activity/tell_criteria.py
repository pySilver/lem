"""The Activity lines for the recorded criteria, their read, and their approval."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views.activity import told

if TYPE_CHECKING:
    from lem.records.journal.task import CriteriaNoted

READERS = "users"
APPROVED = MappingProxyType(
    {
        "owner": "You approved the criteria",
        "read": "The agent froze the criteria from the read",
        "alone": "Lem approved the criteria while you were away",
        "lem": "Lem approved the criteria",
    }
)


SIMPLE = MappingProxyType(
    {
        "read-start": (told.QUIET, "The personas’ read of the criteria started"),
        "skip-asked": (told.YOU, "Lem asked whether to skip the personas’ read"),
        "skip-yes": (told.YOU, "You said to skip the personas’ read"),
    }
)


def criteria(entry: CriteriaNoted) -> told.Told:
    """The criteria event in the words of the feed."""
    match entry.event:
        case "approved":
            by = entry.by or "lem"
            look = told.YOU if by == "owner" else told.LEM
            return told.Told(look, told.CHECK, APPROVED[by], f"approval {entry.number}")
        case "recorded":
            return told.Told(
                told.LEAD,
                told.PAGE,
                "Acceptance criteria recorded",
                f"{entry.number} on the {entry.size} track",
            )
        case "read-done":
            return read(entry)
        case _:
            actor, head = SIMPLE[entry.event]
            return told.Told(actor, READERS, head)


def read(entry: CriteriaNoted) -> told.Told:
    """How many personas answered and whether they raised a doubt."""
    counts = answer_count(entry)
    if not entry.answered:
        return told.Told(
            told.BAD,
            READERS,
            "Nobody answered the personas’ read of the criteria",
            counts,
        )
    look = told.YOU if entry.flagged or entry.split else told.DONE
    flagged = entry.flagged or 0
    notes = (
        "the families split" if entry.split else "",
        f"{flagged} flagged",
        counts,
    )
    return told.Told(
        look, READERS, "The personas read the criteria", " · ".join(filter(None, notes))
    )


def answer_count(entry: CriteriaNoted) -> str:
    """How many of the personas asked gave an answer."""
    asked, answered = entry.asked or 0, entry.answered or 0
    return f"{answered} of {asked} answered"
