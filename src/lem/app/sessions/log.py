"""The file of what Lem did to a task's sessions, `tasks/SLUG/session-acts.jsonl`: one framed line
for each act of `app/sessions/acts.py`, as `store.sessions` writes the lines of `session-start`.

A writer appends a line end, the JSON and a line end in one `os.write`, so two writers never mix
their bytes; a reader skips an empty line and a damaged one. A session is named by agterm's id,
which is matched in no regard to case: agterm prints ids in capitals, and a pane's environment
may hold them in either.
"""

import contextlib
import os
from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions.acts import Act, Open
from lem.store import guard

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

ACTS = "session-acts.jsonl"
# Read and write for the owner, read for the rest, as a file the shell makes.
MODE = 0o644


def append(folder: Path, act: Act) -> None:
    """Append one framed line to the task folder's file of acts; refused in a state folder of
    the Lem before."""
    guard.writable(folder.parents[1])
    frame = b"".join((b"\n", msgspec.json.encode(act), b"\n"))
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    descriptor = os.open(folder / ACTS, flags, MODE)
    with contextlib.ExitStack() as stack:
        stack.callback(os.close, descriptor)
        os.write(descriptor, frame)


def read(folder: Path) -> tuple[Act, ...]:
    """Every readable act of the task folder, in the order written; refused in a state folder
    of the Lem before."""
    guard.readable(folder.parents[1])
    try:
        body = (folder / ACTS).read_bytes()
    except FileNotFoundError:
        return ()
    found = (decoded(raw) for raw in body.split(b"\n") if raw.strip())
    return tuple(act for act in found if act is not None)


def decoded(raw: bytes) -> Act | None:
    """One line, or None when it is damaged."""
    try:
        return msgspec.json.decode(raw, type=Act)
    except msgspec.DecodeError:
        return None


def same(one: str | None, other: str | None) -> bool:
    """Whether two ids name one session of agterm."""
    if not one or not other:
        return False
    return one.upper() == other.upper()


def newest_open(acts: tuple[Act, ...]) -> Open | None:
    """The task's newest session that Lem opened."""
    opens = [act for act in acts if isinstance(act, Open)]
    return opens[-1] if opens else None


def newest_in(folders: Iterable[Path]) -> Open | None:
    """The newest session Lem opened for any of the tasks of `folders`."""
    opens = (newest_open(read(folder)) for folder in folders)
    return max(filter(None, opens), key=lambda opened: opened.at, default=None)


def of_session(acts: tuple[Act, ...], session: str) -> tuple[Act, ...]:
    """The acts that name the session `session`, in their order."""
    return tuple(act for act in acts if same(act.session, session))
