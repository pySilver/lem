"""The files of a task's folder, for its board: every path in it that is a document of the task,
and the prose of its markdown files read as they are (the design's part 3, "Prose and
artifacts")."""

from typing import TYPE_CHECKING

from lem.app.sessions import log
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

# The files of a task's folder that are no document of it: its record, its lock, and Lem's
# acts on its sessions.
OWN = frozenset((tasks.RECORD, tasks.LOCK, log.ACTS))
PROSE = ".md"


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
    """The text of each markdown file of the folder, by its path; a file that does not read
    is left out."""
    names = (name for name in files if name.endswith(PROSE))
    found = ((name, text_of(folder / name)) for name in names)
    return tuple((name, text) for name, text in found if text is not None)


def text_of(path: Path) -> str | None:
    """The text of a file, or None when it does not read."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return None
