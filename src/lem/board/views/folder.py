"""The files of a task's folder, for its board: every path in it that is a document of the task,
and the text of each file the board shows as text, read as it is (the design's part 3, "Prose
and artifacts"): its markdown, its logs, its records and its pages, up to `CAP` bytes each."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from lem.app.sessions import log
from lem.board.views.artifacts import kinds, listing
from lem.board.views.facts import Stat
from lem.store import tasks

if TYPE_CHECKING:
    import os
    from pathlib import Path

# The files of a task's folder that are no document of it: its record, its lock, and Lem's
# acts on its sessions.
OWN = frozenset((tasks.RECORD, tasks.LOCK, log.ACTS))
# The kinds the board shows by link or image only.
UNSHOWN = frozenset((kinds.BINARY, kinds.IMAGE))
# A file over this many bytes is listed with no text: the page draws each file it shows, and a
# review tool's log can be megabytes. A guess, not a measurement (`artifacts.CAP` on `main`).
CAP = 300_000


def files_of(folder: Path) -> tuple[str, ...]:
    """Every file under the task's folder, by its path in it, in order; none when the folder
    is not there."""
    if not folder.is_dir():
        return ()
    paths = (path for path in folder.rglob("*") if path.is_file())
    names = (path.relative_to(folder).as_posix() for path in paths)
    return tuple(sorted(name for name in names if name not in OWN))


type Prose = tuple[tuple[str, str], ...]


def prose_of(folder: Path, files: tuple[str, ...]) -> Prose:
    """The text of each previewable file of the folder, by its path; a file that does not read
    is left out."""
    names = (
        name
        for name in files
        if listing.listed(name) and kinds.kind_of(name) not in UNSHOWN
    )
    found = ((name, text_of(folder, name)) for name in names)
    return tuple((name, text) for name, text in found if text is not None)


def text_of(folder: Path, name: str) -> str | None:
    """The text of a file within its folder, up to `CAP` bytes."""
    path = (folder / name).resolve()
    if not path.is_relative_to(folder.resolve()) or size_of(path) > CAP:
        return None
    try:
        body = path.read_bytes()
    except OSError:
        return None
    return None if b"\x00" in body else body.decode(errors="replace")


def size_of(path: Path) -> int:
    """The bytes of a file, or none past the cap when it does not read."""
    try:
        return path.stat().st_size
    except OSError:
        return CAP + 1


def stats_of(folder: Path, files: tuple[str, ...]) -> tuple[Stat, ...]:
    """The size and the time of each file of the folder that still reads."""
    found = ((name, stat_of(folder / name)) for name in files)
    return tuple(
        Stat(path=name, size=stat.st_size, changed=moment_of(stat.st_mtime))
        for name, stat in found
        if stat is not None
    )


def stat_of(path: Path) -> os.stat_result | None:
    """A file's facts, or None when it is gone."""
    try:
        return path.stat()
    except OSError:
        return None


def moment_of(stamp: float) -> datetime:
    """A file's time as a moment."""
    return datetime.fromtimestamp(stamp, tz=UTC)
