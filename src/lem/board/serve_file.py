"""`serve.json` in Lem's home folder: the facts of the server that runs, written whole at its
start and removed at its clean stop, so that a command reads whether one runs with no connect.
The write marks the home folder as this Lem's, or is refused beside the files of Lem 0.3; the
removal removes only a file this Lem wrote there.
"""

import contextlib
from typing import TYPE_CHECKING

import msgspec

from lem.board.facts import Facts
from lem.kernel import files, folders

if TYPE_CHECKING:
    from pathlib import Path

SERVE = "serve.json"


def write(home: Path, facts: Facts) -> None:
    """Write the facts of the server that starts now."""
    folders.home_marked(home)
    files.write_whole(home / SERVE, msgspec.json.encode(facts))


def read(home: Path) -> Facts | None:
    """The facts the file holds; None when there is none or it does not read."""
    try:
        return msgspec.json.decode((home / SERVE).read_bytes(), type=Facts)
    except OSError, msgspec.DecodeError:
        return None


def remove(home: Path, pid: int) -> None:
    """Remove the file at a clean stop, only while it still names the process `pid`: a server
    that replaced this one keeps its own."""
    found = read(home)
    if found is not None and found.pid == pid:
        with contextlib.suppress(FileNotFoundError):
            (home / SERVE).unlink()
