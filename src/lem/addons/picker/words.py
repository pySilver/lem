"""A picker row's words: the task's ask in the owner's words, and its state in the board's words,
its track, the age of its state and its pull request (`picker.label`, `state_words`, `age` and
`pull_request` on `main`)."""

import datetime as dt
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked, ReleaseHold

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task

# The state of a task in the board's words (`board_model.STATUS` on `main`).
STATUS = MappingProxyType(
    {
        "queued": "Queued",
        "shaping": "Shaping",
        "building": "Building",
        "planned": "Planned",
        "ready": "Ready for its checks",
        "landing": "Checks and review",
        "open": "Waits for the merge",
        "landed": "Landed",
        "answered": "Answered",
        "dropped": "Dropped",
    }
)
TRACKS = MappingProxyType({"small": "fast track", "full": "standard track"})
INVESTIGATING = "Investigating"
# The longest label, in characters, before it ends in an ellipsis.
LABEL_WIDTH = 100
MINUTE = dt.timedelta(minutes=1)
HOUR = dt.timedelta(hours=1)
DAY = dt.timedelta(days=1)
# The units of an age, the longest first.
UNITS = ((DAY, "d"), (HOUR, "h"), (MINUTE, "m"))


def label(task: Task) -> str:
    """The task's ask in the owner's words on one line, its slug in words when it has none;
    agterm refuses a label with a control character, so none stays."""
    words = " ".join(printable(task.ask).split())
    if not words:
        words = task.slug.replace("-", " ").capitalize()
    if len(words) <= LABEL_WIDTH:
        return words
    short = words[: LABEL_WIDTH - 1].rstrip()
    return f"{short}…"


def printable(text: str) -> str:
    """`text` with a space for each character that does not print."""
    return "".join(ch if ch.isprintable() else " " for ch in text)


def state_words(task: Task) -> str:
    """The task's state in the board's words: what holds it first, then an investigation
    before any lead, then its status."""
    hold = task.hold
    if isinstance(hold, Parked):
        return "Parked"
    if isinstance(hold, Blocked | ReleaseHold):
        return "Blocked"
    if isinstance(hold, OwnerHold | BreakerHold):
        return "Waits for you"
    then = task.shape.then if task.shape else None
    if task.status == "building" and then == "investigation" and task.lead is None:
        return INVESTIGATING
    return STATUS[task.status]


def age(since: dt.datetime, now: dt.datetime) -> str:
    """How long ago the state began, in the shortest words: now, 5m, 3h, 2d."""
    passed = now - since
    if passed < MINUTE:
        return "now"
    longer = (pair for pair in UNITS if passed >= pair[0])
    unit, letter = next(longer)
    count = passed // unit
    return f"{count}{letter}"


def pull_words(record: Record) -> str:
    """The pull request's number and green or not green; only green or not green with no
    number, and nothing before a proposal."""
    landing = record.landing
    proposed = landing.proposed if landing else None
    if landing is None or proposed is None:
        return ""
    word = "green" if proposed.green else "not green"
    if landing.pull is None:
        return word
    number = landing.pull.number
    return f"#{number} {word}"
