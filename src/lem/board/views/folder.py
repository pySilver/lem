"""The files of a task's folder, for its board: every path in it that is a document of the task,
and the text of each file the board shows as text, read as it is (the design's part 3, "Prose
and artifacts"): its markdown, its logs, its records and its pages, up to `CAP` bytes each."""

from datetime import UTC, datetime
from stat import S_ISREG
from typing import TYPE_CHECKING

from lem.app.sessions import log
from lem.board.views.artifacts import kinds, listing
from lem.board.views.facts import PlanFile, Stat
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.work import Plan

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
    found = (stat_of(folder / name, name) for name in files)
    return tuple(stat for stat in found if stat is not None)


def stat_of(path: Path, name: str) -> Stat | None:
    """A regular file's facts, with its name relative to the folder that holds it."""
    try:
        found = path.stat()
    except OSError:
        return None
    if not S_ISREG(found.st_mode):
        return None
    changed = datetime.fromtimestamp(found.st_mtime, tz=UTC)
    return Stat(path=name, size=found.st_size, changed=changed)


def plan_of(worktree: Path, plan: Plan | None) -> PlanFile | None:
    """The recorded plan of the task, in its own worktree."""
    if plan is None or not (worktree / ".git").exists():
        return None
    path = (worktree / plan.path).resolve()
    if not path.is_relative_to(worktree.resolve()):
        return None
    stat = stat_of(path, plan.path)
    if stat is None or not stat.size:
        return None
    return PlanFile(stat=stat, text=text_of(worktree, plan.path))
