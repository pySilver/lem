"""What a resume carries from a dropped task's folder into the new task's (`project.RESUMED_FILES`
and `resumed_reads` on `main`): the documents a fresh agent goes on from, each breaker's
document, the breaker's pictures, and the brief with the new task's own lines.

Every file is read whole before anything is written, so a file that does not read makes nothing.
The records the landing reads (criteria, decisions, the plan talk, the investigation) are fields
of the task's record now, which the resume copies; the landing's own files stay with the old task.
"""

from typing import TYPE_CHECKING, NamedTuple

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

NOTES = (
    "task.md",
    "talk.md",
    "directions.md",
    "interview-notes.md",
    "scout.md",
    "investigation.md",
    "outside.md",
    "criteria.md",
    "criteria-read.md",
    "handoff.md",
)
BREAKERS = "breaker-*.md"
MEDIA = "media"
BRIEF = "brief.md"


class Taken(NamedTuple):
    """What a resume took of the dropped task's folder: its files and its brief."""

    files: dict[str, bytes]
    brief: str | None


def unreadable(path: Path, error: OSError | UnicodeDecodeError) -> Refusal:
    """The refusal of a resume whose file does not read: it made nothing."""
    return Refusal(
        "unreadable",
        f"resume reads every file it carries before it writes, and {path} does not read "
        f"({error}), so it made nothing",
        "make it readable, then resume again",
    )


def read_whole(folder: Path) -> dict[str, bytes]:
    """The files a resume carries from `folder`, each by its path in it, read whole."""
    paths = [folder / name for name in NOTES if (folder / name).is_file()]
    paths += sorted(folder.glob(BREAKERS))
    media = folder / MEDIA
    if media.is_dir():
        paths += sorted(path for path in media.rglob("*") if path.is_file())
    carried: dict[str, bytes] = {}
    for path in paths:
        try:
            carried[path.relative_to(folder).as_posix()] = path.read_bytes()
        except OSError as error:
            raise unreadable(path, error) from error
    return carried


def brief_of(folder: Path) -> str | None:
    """The dropped task's brief as text, or None; refused when it is not UTF-8."""
    path = folder / BRIEF
    if not path.is_file():
        return None
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise unreadable(path, error) from error


def rebriefed(brief: str, own: dict[str, str], resumed: str) -> str:
    """The old brief with the new task's own lines, and the line it was resumed from."""
    rows = brief.splitlines()
    named = (row.split(":", 1)[0] for row in rows)
    kept = [
        f"{name}: {own[name]}" if name in own else row
        for row, name in zip(rows, named, strict=True)
    ]
    return "\n".join((*kept, resumed, ""))


def taken(folder: Path) -> Taken:
    """Everything a resume carries from `folder`, read whole before any write."""
    return Taken(files=read_whole(folder), brief=brief_of(folder))


def written(target: Path, carried: dict[str, bytes]) -> None:
    """Write the carried files into the new task's folder."""
    for name, body in carried.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
