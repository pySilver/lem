"""The machine's line of the runs of the checks that wait, in Lem's home folder: `load.line/`
holds one file for each run that waits, `PID.json`, locked by that run for its whole wait, and
`load.lock` is held by one look at a time and keeps the last start (`land.line_join`,
`line_leave`, `line_live` and `line_wanted` on `main`).

An entry is live while a process holds its file's lock, however late its look comes; a lock that
a shared try takes is held by no process, so its run is gone (it ended, was stopped or killed,
or died in the middle of its write), and its file is removed. A run that is killed leaves the
line by the lock it loses.
"""

import contextlib
import dataclasses
import fcntl
from typing import IO, TYPE_CHECKING

import msgspec

from lem.kernel import locks
from lem.kernel.errors import Refusal
from lem.model.landing import checks_line

if TYPE_CHECKING:
    from pathlib import Path


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Own:
    """This run's place in the line: its entry, its file, and the open file that holds it."""

    entry: checks_line.Entry
    path: Path
    stream: IO[str]


def joined(folder: Path, entry: checks_line.Entry, pid: int) -> Own:
    """The run's own entry, made under the hold of `load.lock`: its file `PID.json`, locked
    for the whole wait and written whole once."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{pid}.json"
    stream = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        stream.close()
        raise Refusal(
            "line",
            f"the line of the load gate holds {path} for a run that still waits, with this "
            f"process's id {pid}",
            "`lem land checks SLUG --status` of the task says which run waits",
        ) from None
    stream.seek(0)
    stream.truncate()
    stream.write(msgspec.json.encode(entry).decode())
    stream.flush()
    return Own(entry=entry, path=path, stream=stream)


def leave(own: Own) -> None:
    """The run leaves the line: its file goes, then its lock with the open file. A reader that
    opened the file before it went reads it as held, and one that opens it after finds none."""
    with contextlib.suppress(FileNotFoundError):
        own.path.unlink()
    own.stream.close()


def held(path: Path) -> checks_line.Entry | None:
    """The entry of `path` while a run holds it; None, and the file removed, when none does.
    The look takes the lock itself when no run holds it, as a shared try would."""
    try:
        stream = path.open("r", encoding="utf-8")
    except FileNotFoundError:
        return None
    with stream:
        if locks.taken(stream):
            with contextlib.suppress(FileNotFoundError):
                path.unlink()
            return None
        return entry_of(stream.read())


def entry_of(text: str) -> checks_line.Entry | None:
    """A held file's entry; a file that does not read is no run."""
    try:
        return msgspec.json.decode(text, type=checks_line.Entry)
    except msgspec.DecodeError:
        return None


def live(folder: Path, own: Own) -> checks_line.Line:
    """The runs that wait, this one last, under the hold of `load.lock`."""
    paths = sorted(folder.glob("*.json"))
    others = (held(path) for path in paths if path != own.path)
    return (*(entry for entry in others if entry is not None), own.entry)
