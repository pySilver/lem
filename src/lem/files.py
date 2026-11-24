"""A file written whole, and a file held by threads and processes alike: the one writer
that `land.py`, `criteria.py`, `project.py`, `inbox.py` and `experts.py` share, and
the one lock of `push.py` and `inbox.py`.

A reader of a record, a pull request's text or a plan finds the old file or the new
one, never a part: the text goes to a file beside it under another name, which then
replaces it in one rename. The other name is the caller's, and it is part of what the
caller does: two writers of one file at one moment must never write one other file, so
it holds the process's id, and the board server's threads, which share that id, add
their own (`inbox.py`); a check looks for what a writer left (`lem-land-guards.sh`
finds no `whole.txt*.new`). So a caller that has a scheme of its own passes the name,
and the rest take `NAME.PID.new` beside the file. A caller that may write the first
file of a folder says so (`make_folder`); the others write into a folder that is there.

A file that the board server's threads write, and a command in a process of its own
too, is held under two locks at once (`held`): a thread lock, which keeps out the other
threads of the one process, and a lock file beside it, which keeps out the other
processes. Each such file has a thread lock of its own (`push.py`'s and
`inbox.py`'s).

It imports nothing of Lem's, so that any script may load it.
"""

import contextlib
import fcntl
import json
import os

# typing's flag, without the import of typing, which a hook's start does not pay
TYPE_CHECKING = False
if TYPE_CHECKING:
    import threading
    from collections.abc import Generator
    from pathlib import Path


def write_whole(
    path: Path, text: str, *, fresh: Path | None = None, make_folder: bool = False
) -> None:
    """Write TEXT as PATH whole or not at all: under FRESH first, `NAME.PID.new` beside
    PATH unless named, then renamed over PATH. With MAKE_FOLDER, PATH's folder is made
    first when it is not there."""
    if make_folder:
        path.parent.mkdir(parents=True, exist_ok=True)
    staging = fresh or path.with_name(f"{path.name}.{os.getpid()}.new")
    staging.write_text(text, encoding="utf-8")
    staging.replace(path)


def write_json(
    path: Path, record: object, *, fresh: Path | None = None, make_folder: bool = False
) -> None:
    """Write RECORD as PATH whole, as JSON in the one form of Lem's records: two spaces
    of indent, every character as itself, and a line end after it."""
    write_whole(
        path,
        f"{json.dumps(record, indent=2, ensure_ascii=False)}\n",
        fresh=fresh,
        make_folder=make_folder,
    )


@contextlib.contextmanager
def held(lock: threading.Lock, path: Path) -> Generator[None]:
    """Hold LOCK, this process's lock of a file, and then PATH, the lock file of the
    same, waiting for another holder of either; PATH's folder is made first when it is
    not there."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with lock, path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)
