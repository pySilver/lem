"""The signs of work of a Claude Code transcript, for the `Harness` port on Claude Code
(`harness_claude`): its newest sign, and whether its turn runs, over its records newest first.

The newest sign is the `timestamp` of the newest `user` or `assistant` record that runs a turn,
never the file's time: a message that reaches an idle pane writes a `queue-operation` record and
runs none, and `attachment`, `system`, `cost-state`, `continued-in` and `api-request` records are
none either.

The turn is read from the newest decisive record that is not a subagent's (a sidechain). An
`assistant` record that stopped on a tool runs, but on the question widget, which asks the owner
and so ended; one that stopped on anything else (`end_turn`, `stop_sequence`, `refusal`,
`max_tokens`) ended, and one with no stop decides nothing. A `user` record that is an interrupt
ended; a local command's text and a compaction's summary decide nothing, since none runs a turn;
any other (a prompt, a tool's result, a task notification, a skill's text) runs.

Three probes of 2026-11-23 over the 300 newest transcripts on the owner's Mac, Claude Code
2.1.294 to 2.1.330 (`signs.py` on `main`): the main thread's assistant records stopped 53,528
times on `tool_use`, 5,411 on `end_turn`, 29 on `stop_sequence`, 3 on null and 1 on `refusal`;
a `turn_duration` record followed 4,114 of 4,122 ended turns but none of 8 interrupts, so it is no
mark of an end; and Claude Code's own `status` in `sessions/PID.json` read `busy` for 4 of 26 live
sessions whose transcript had ended on `end_turn`, so it is no mark of a running turn.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Iterable

    from lem.adapters.claude_transcript import Entry

type Turn = Literal["runs", "ended"]

# The record types that are a turn of the session.
TURNS = frozenset(("user", "assistant"))
# The question widget's tool: a turn that stops on it waits for the owner.
ASKS = "AskUserQuestion"
# The text a local command puts into a user record, and the one of an interrupt.
LOCAL = (
    "<command-name>",
    "<command-message>",
    "<command-args>",
    "<local-command-",
    "<bash-input>",
    "<bash-stdout>",
    "<bash-stderr>",
)
INTERRUPT = "[Request interrupted"


def newest_sign(records: Iterable[Entry]) -> datetime | None:
    """The time of the newest record of `records`, newest first, that runs a turn."""
    turns = (each for each in records if is_turn(each))
    stamps = (moment(each.timestamp) for each in turns)
    return next((stamp for stamp in stamps if stamp is not None), None)


def moment(stamp: str | None) -> datetime | None:
    """The UTC moment of a record's time, to the second, or None for one that is not there or
    does not read: such a record gives no sign."""
    try:
        found = datetime.fromisoformat(stamp or "")
    except ValueError:
        return None
    zoned = found if found.tzinfo else found.replace(tzinfo=UTC)
    return zoned.astimezone(UTC).replace(microsecond=0)


def turn_of(records: Iterable[Entry]) -> Turn | None:
    """Whether the session's newest turn runs or ended, by its newest decisive record of
    `records`, newest first; None when no record decides."""
    own = (each for each in records if not each.sidechain)
    decided = (assistant_turn(each) or user_turn(each) for each in own)
    return next((turn for turn in decided if turn), None)


def assistant_turn(entry: Entry) -> Turn | None:
    """What an `assistant` record says: it runs while it stopped on a tool but the question
    widget, and ended on any other stop; None for another record, or one with no stop."""
    reason = entry.message.stop_reason if entry.message else None
    if entry.kind != "assistant" or not reason:
        return None
    body = entry.message.body if entry.message else None
    parts = body if isinstance(body, tuple) else ()
    calls = (part.name for part in parts if part.kind == "tool_use")
    asked = ASKS in calls
    return "runs" if reason == "tool_use" and not asked else "ended"


def user_turn(entry: Entry) -> Turn | None:
    """What a `user` record says: an interrupt ended the turn, a local command's text and a
    compaction's summary decide nothing, and any other record runs it."""
    if entry.kind != "user":
        return None
    if any(text.startswith(INTERRUPT) for text in texts_of(entry)):
        return "ended"
    return "runs" if is_turn(entry) else None


def is_turn(entry: Entry) -> bool:
    """Whether a record is a turn of the session: a `user` or `assistant` record, but a local
    command's text and a compaction's summary, which run none."""
    if entry.kind != "user":
        return entry.kind in TURNS
    texts = texts_of(entry)
    return not entry.compacted and not (texts and texts[0].startswith(LOCAL))


def texts_of(entry: Entry) -> tuple[str, ...]:
    """The text of a record's message: its content when that is a text, else each of its text
    parts."""
    body = entry.message.body if entry.message else None
    if isinstance(body, str):
        return (body,)
    parts = body or ()
    texts = (part.text for part in parts if part.kind == "text")
    return tuple(text for text in texts if text)
