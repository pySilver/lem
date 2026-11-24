"""A file written whole, and a file held by threads and processes alike: the one writer
that `land.py`, `criteria.py`, `project.py`, `lem_inbox.py` and `experts.py` share, and
the one lock of `lem_push.py` and `lem_inbox.py`.

A reader of a record, a pull request's text or a plan finds the old file or the new
one, never a part: the text goes to a file beside it under another name, which then
replaces it in one rename. The other name is the caller's, and it is part of what the
caller does: two writers of one file at one moment must never write one other file, so
it holds the process's id, and the board server's threads, which share that id, add
their own (`lem_inbox.py`); a check looks for what a writer left (`lem-land-guards.sh`
finds no `whole.txt*.new`). So a caller that has a scheme of its own passes the name,
and the rest take `NAME.PID.new` beside the file. A caller that may write the first
file of a folder says so (`make_folder`); the others write into a folder that is there.

A file that the board server's threads write, and a command in a process of its own
too, is held under two locks at once (`held`): a thread lock, which keeps out the other
threads of the one process, and a lock file beside it, which keeps out the other
processes. Each such file has a thread lock of its own (`lem_push.py`'s and
`lem_inbox.py`'s).

It imports nothing of Lem's, so that any script may load it.
"""

import contextlib
import fcntl
import json
import os
import threading
from collections.abc import Generator
from pathlib import Path


def write_whole(
    file: Path, text: str, *, fresh: Path | None = None, make_folder: bool = False
) -> None:
    """Write TEXT as FILE whole or not at all: under FRESH first, `NAME.PID.new` beside
    FILE unless named, then renamed over FILE. With MAKE_FOLDER, FILE's folder is made
    first when it is not there."""
    if make_folder:
        file.parent.mkdir(parents=True, exist_ok=True)
    staging = fresh or file.with_name(f"{file.name}.{os.getpid()}.new")
    staging.write_text(text, encoding="utf-8")
    staging.replace(file)


def write_json(
    file: Path, data: object, *, fresh: Path | None = None, make_folder: bool = False
) -> None:
    """Write DATA as FILE whole, as JSON in the one form of Lem's records: two spaces
    of indent, every character as itself, and a line end after it."""
    write_whole(
        file,
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        fresh=fresh,
        make_folder=make_folder,
    )


@contextlib.contextmanager
def held(lock: threading.Lock, file: Path) -> Generator[None, None, None]:
    """Hold LOCK, this process's lock of a file, and then FILE, the lock file of the
    same, waiting for another holder of either; FILE's folder is made first when it is
    not there."""
    file.parent.mkdir(parents=True, exist_ok=True)
    with lock, file.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
