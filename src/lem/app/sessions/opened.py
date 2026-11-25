"""The sessions Lem opened and closed for a task: `tasks/SLUG/opened.jsonl`, one framed line
each, as `store.sessions` writes the lines of `session-start`.

A stand-in of this slice: the task's journal has no entry for a session's open or close yet
(`notes/slice-session.md` asks `records` for them), so the opens and closes live in their own
file until the step `sessions` moves them into the journal. Each line names the agterm session,
and an open its name, the phase it opened in, why, and the workspace.
"""

import contextlib
import os
from typing import TYPE_CHECKING, Literal

import msgspec

from lem.records.base import Moment, Tagged

if TYPE_CHECKING:
    from pathlib import Path

OPENED = "opened.jsonl"
# Read and write for the owner, read for the rest, as a file the shell makes.
MODE = 0o644


class Open(Tagged, tag="open", frozen=True, kw_only=True):
    """A session Lem opened for the task."""

    at: Moment
    session: str
    name: str
    phase: str
    why: str
    workspace: str | None = None


class Close(Tagged, tag="close", frozen=True, kw_only=True):
    """A session of the task that Lem closed, or found gone, and why."""

    at: Moment
    session: str
    why: Literal["handoff", "ended", "owner"]


type Noted = Open | Close


def append(folder: Path, noted: Noted) -> None:
    """Append one framed line to the task folder's file of sessions opened and closed."""
    frame = b"".join((b"\n", msgspec.json.encode(noted), b"\n"))
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    descriptor = os.open(folder / OPENED, flags, MODE)
    with contextlib.ExitStack() as stack:
        stack.callback(os.close, descriptor)
        os.write(descriptor, frame)


def read(folder: Path) -> tuple[Noted, ...]:
    """Every readable line of the task folder's file, in the order written."""
    try:
        body = (folder / OPENED).read_bytes()
    except FileNotFoundError:
        return ()
    decoded = (decoded_line(raw) for raw in body.split(b"\n") if raw.strip())
    return tuple(noted for noted in decoded if noted is not None)


def decoded_line(raw: bytes) -> Noted | None:
    """One line, or None when it is damaged."""
    try:
        return msgspec.json.decode(raw, type=Noted)
    except msgspec.DecodeError:
        return None


def newest_open(noted: tuple[Noted, ...]) -> Open | None:
    """The task's newest session that Lem opened."""
    opens = [line for line in noted if isinstance(line, Open)]
    return opens[-1] if opens else None
