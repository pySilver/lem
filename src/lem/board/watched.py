"""What an open page's stream looks at, at each tick: every file the board's pages read beside
the task records, so that a change of one sends the page a refresh too (`Look` and `listed` of
`serve.py` on `main`).

The look is a digest of each file's name, inode, size and change time: the tasks' records, the
state folder's demo mark, the server's look at the forge, the Inbox's record and the reviewer's
items, the workspace's two settings files of Lem, the owner's mark in Lem's home folder, and with
a task open each file of that task's folder, so that an artifact written with no record's change
still shows.
"""

import contextlib
import hashlib
from typing import TYPE_CHECKING

from lem.settings import placed
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

# The files of the state folder the pages read beside the records, and the globs of folders.
STATE_FILES = ("demo", "forge.json", "inbox.json")
STATE_GLOBS = ("tasks/*/task.json", "backlog/*")
BACKLOG = dict(placed.FIXED)["backlog"]
SETTINGS = ("settings.toml", "settings.local.toml")
OWNER = "owner.json"
DIGITS = 16

type Stamp = tuple[str, int, int, int]


def stamp(path: Path) -> Stamp | None:
    """A file's path, inode, size and change time; None when it is not there."""
    with contextlib.suppress(OSError):
        facts = path.stat()
        return (str(path), facts.st_ino, facts.st_size, facts.st_mtime_ns)
    return None


def paths_of(state: Path, home: Path, task: str | None) -> Iterable[Path]:
    """Every file the look stamps."""
    lem = state.parent
    yield from (state / name for name in STATE_FILES)
    for pattern in STATE_GLOBS:
        yield from state.glob(pattern)
    yield from (lem.parent / BACKLOG).glob("*.md")
    yield from (lem / name for name in SETTINGS)
    yield home / OWNER
    if task and places.SLUG.fullmatch(task):
        yield from (state / "tasks" / task).rglob("*")


def look(state: Path, home: Path, task: str | None = None) -> str:
    """The digest of every file the look stamps: it moves when one of them changes."""
    found = map(stamp, paths_of(state, home, task))
    stamps = sorted(filter(None, found))
    digest = hashlib.sha256(repr(stamps).encode())
    return digest.hexdigest()[:DIGITS]
