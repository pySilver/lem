"""The correction queue of one repository, in the state folder of its main checkout, which every
worktree shares and git never sees (`corrections.py` on `main`).

`corrections.jsonl` holds each correction Jev flagged, `corrections-reviews.jsonl` what a retro
decided about each, and `corrections.log` each failure of the hook or the worker, never shown in
a conversation. Each is one JSON object a line, appended in one write; a line that does not read
is named with its file and number, and the rest of the file is not guessed at.
"""

import contextlib
import os
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

QUEUE = "corrections.jsonl"
REVIEWS = "corrections-reviews.jsonl"
LOG = "corrections.log"
WAITING = "corrections-waiting"
# Read and write for the owner alone: the queue holds his words.
OWNER_FILE = 0o600


class LogLine(Frozen, frozen=True, kw_only=True):
    """One line of the log: when, the session, and an error (the message was never judged) or
    a note (it was)."""

    at: str
    session: str | None = None
    error: str | None = None
    note: str | None = None


def lines[Shape](path: Path, shape: type[Shape]) -> tuple[Shape, ...]:
    """Every record of one of the queue's files, none when it is not there; refused at a line
    that is not UTF-8 or does not read."""
    try:
        body = path.read_bytes()
    except FileNotFoundError:
        return ()
    found = (
        line_of(path, number, raw, shape)
        for number, raw in enumerate(body.split(b"\n"), 1)
        if raw.strip()
    )
    return tuple(found)


def line_of[Shape](path: Path, number: int, raw: bytes, shape: type[Shape]) -> Shape:
    """One line of a queue's file as `shape`; refused with its file and number."""
    try:
        return msgspec.json.decode(raw.decode("utf-8"), type=shape)
    except (UnicodeDecodeError, msgspec.DecodeError) as error:
        raise Refusal(
            "queue-line",
            f"{path}:{number} does not read ({error})",
            "Lem writes the file: correct or remove that line by hand",
        ) from error


def appended(path: Path, line: msgspec.Struct) -> None:
    """Append one record as one line, in one write, to a file the owner alone reads."""
    body = b"".join((msgspec.json.encode(line), b"\n"))
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    descriptor = os.open(path, flags, OWNER_FILE)
    with contextlib.ExitStack() as stack:
        stack.callback(os.close, descriptor)
        os.write(descriptor, body)
