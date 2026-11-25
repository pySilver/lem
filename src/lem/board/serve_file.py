"""`serve.json` in Lem's home folder: the facts of the server that runs, written whole at its
start and removed at its clean stop, so that a command reads whether one runs with no connect.
"""

import contextlib
from typing import TYPE_CHECKING

import msgspec

from lem.board.facts import Facts
from lem.kernel import files

if TYPE_CHECKING:
    from pathlib import Path

SERVE = "serve.json"


def write(home: Path, facts: Facts) -> None:
    """Write the facts of the server that starts now."""
    home.mkdir(parents=True, exist_ok=True)
    files.write_whole(home / SERVE, msgspec.json.encode(facts))


def remove(home: Path, pid: int) -> None:
    """Remove the file at a clean stop, only while it still names the process `pid`: a server
    that replaced this one keeps its own."""
    path = home / SERVE
    try:
        named = msgspec.json.decode(path.read_bytes(), type=Facts).pid
    except OSError, msgspec.DecodeError:
        return
    if named == pid:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
