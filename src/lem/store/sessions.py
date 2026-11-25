"""`tasks/SLUG/sessions.jsonl`: the sessions of a task, one framed line each (the design's
part 3).

A writer appends a line end, the JSON and a line end in one `os.write` on a file opened to
append, so that two writers never mix their bytes and a line cut off by a crash ends at the next
writer's frame. A reader splits at the line end alone and skips an empty line, a damaged one,
and one of another form.
The `session-start` hook writes the same frame with the standard library (`lem.hooks`).
"""

import contextlib
import os
from typing import TYPE_CHECKING

import msgspec

from lem.records.sessions import VERSION, SessionLine

if TYPE_CHECKING:
    from pathlib import Path

SESSIONS = "sessions.jsonl"
# Read and write for the owner, read for the rest, as a file the shell makes.
MODE = 0o644


def append(folder: Path, line: SessionLine) -> None:
    """Append one framed line to the task folder's sessions file."""
    frame = b"".join((b"\n", msgspec.json.encode(line), b"\n"))
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    descriptor = os.open(folder / SESSIONS, flags, MODE)
    with contextlib.ExitStack() as stack:
        stack.callback(os.close, descriptor)
        os.write(descriptor, frame)


def decoded(raw: bytes) -> SessionLine | None:
    """One line as a session, or None when it is damaged or of another form."""
    try:
        line = msgspec.json.decode(raw, type=SessionLine)
    except msgspec.DecodeError:
        return None
    return line if line.version == VERSION else None


def read(folder: Path) -> tuple[SessionLine, ...]:
    """Every readable session of the task folder, in the order written."""
    try:
        body = (folder / SESSIONS).read_bytes()
    except FileNotFoundError:
        return ()
    lines = (decoded(raw) for raw in body.split(b"\n") if raw.strip())
    return tuple(line for line in lines if line is not None)
