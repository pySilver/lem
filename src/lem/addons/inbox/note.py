"""Explain why a wait reaches the owner as a board link."""

from typing import TYPE_CHECKING

from lem.addons.inbox import merges
from lem.model.owner import verbs

if TYPE_CHECKING:
    from lem.addons.inbox.source import RowFacts


def note(found: RowFacts) -> str:
    """Say what prevents the task from taking an Inbox answer."""
    row = found.row
    if row.say:
        return row.say
    if row.kind == "stopped":
        return stopped(found)
    if row.kind == "merge":
        return merge_note(found)
    if row.deaf:
        return "The session does not answer a wake from Lem. The board shows what the owner can do."
    record = found.look.record
    return row.why or verbs.verb(row, record.task, record.landing)


def stopped(found: RowFacts) -> str:
    """Distinguish an unreadable stop from a confirmed stopped replacement."""
    row = found.row
    if row.unread:
        return (
            "Lem could not read the stopped session. Open a fresh session on the board."
        )
    if row.restarted:
        return "The session stopped. Its replacement also stopped."
    return "The session stopped. The owner can open a fresh session on the board."


def merge_note(found: RowFacts) -> str:
    """A refused or unreviewed merge provides a board link only."""
    refused = merges.refusal_of(found)
    if refused:
        return f"The merge did not go through: {refused.line}"
    return "The owner can check the pull request and its merge review on the board."
