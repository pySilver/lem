"""The signs of work of a Claude Code transcript, for the `Harness` port on Claude Code
(`harness_claude`): its newest sign, and whether its turn runs.

The newest sign is the `timestamp` of the newest `user` or `assistant` record. The turn is read
from the newest decisive record that is not a subagent's (a sidechain): an `assistant` record
that stopped on a tool runs, but on the question widget, which asks the owner; one that stopped
on anything else ended. A `user` record that is an interrupt ended, a local command's text
decides nothing, and any other runs (the forms read on the owner's Mac with Claude Code 2.1.294
to 2.1.330, 2026-11-22 and 23). Only the transcript's end is read.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from lem.adapters import claude_transcript

if TYPE_CHECKING:
    from pathlib import Path

type Turn = Literal["runs", "ended"]

# How much of a transcript's end the signs read, in bytes. A guess: a turn writes a few
# kilobytes, and a sign older than this end is no sign of work now.
TAIL = 1048576
# The question widget's tool: a turn that stops on it waits for the owner.
ASKS = "AskUserQuestion"
# The text a local command puts into a user record, and the one of an interrupt.
LOCAL = ("<command-name>", "<command-message>", "<command-args>", "<local-command-")
INTERRUPT = "[Request interrupted"


def newest_first(transcript: Path) -> list[claude_transcript.Entry]:
    """The records of the transcript's end, newest first; none when it does not read."""
    try:
        with transcript.open("rb") as stream:
            stream.seek(max(0, transcript.stat().st_size - TAIL))
            tail = stream.read()
    except OSError:
        return []
    return list(claude_transcript.entries(reversed(tail.split(b"\n"))))


def newest_sign(records: list[claude_transcript.Entry]) -> datetime | None:
    """The time of the newest `user` or `assistant` record of `records`, newest first."""
    turns = (entry for entry in records if entry.kind in {"user", "assistant"})
    stamps = (moment(entry.timestamp) for entry in turns)
    return next((stamp for stamp in stamps if stamp is not None), None)


def moment(stamp: str | None) -> datetime | None:
    """The UTC moment of a record's time, or None for one that is not there or does not
    read: such a record gives no sign."""
    try:
        found = datetime.fromisoformat(stamp or "")
    except ValueError:
        return None
    return found if found.tzinfo else found.replace(tzinfo=UTC)


def turn_of(records: list[claude_transcript.Entry]) -> Turn | None:
    """Whether the session's newest turn runs or ended, by its newest decisive record of
    `records`, newest first."""
    own = (entry for entry in records if not entry.sidechain)
    decided = (assistant_turn(entry) or user_turn(entry) for entry in own)
    return next((turn for turn in decided if turn), None)


def assistant_turn(entry: claude_transcript.Entry) -> Turn | None:
    """What an `assistant` record says: it runs while it stopped on a tool but the question
    widget, and ended on any other stop; None for another record, or one with no stop."""
    reason = entry.message.stop_reason if entry.message else None
    if entry.kind != "assistant" or not reason:
        return None
    body = entry.message.body if entry.message else None
    parts = body if isinstance(body, tuple) else ()
    asked = any(part.name == ASKS for part in parts)
    return "runs" if reason == "tool_use" and not asked else "ended"


def user_turn(entry: claude_transcript.Entry) -> Turn | None:
    """What a `user` record says: an interrupt ended the turn, a local command's text decides
    nothing, and any other record runs it."""
    if entry.kind != "user":
        return None
    text = text_of(entry)
    if text.startswith(INTERRUPT):
        return "ended"
    return None if text.startswith(LOCAL) else "runs"


def text_of(entry: claude_transcript.Entry) -> str:
    """The text of a record's message: its content when that is a text, else its text parts
    joined by line ends."""
    body = entry.message.body if entry.message else None
    if isinstance(body, str):
        return body
    return "\n".join(part.text or "" for part in body or ())
