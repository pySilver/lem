"""The files whose stamps a board's stream reads."""

import contextlib
import hashlib
import re
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
RECORDS = "tasks/*/task.json"
DIGITS = 16
SHARED = (
    "demo",
    "forge.json",
    "inbox.json",
    "backlog/*.md",
    "tasks/*/sessions.jsonl",
    "tasks/*/session-acts.jsonl",
)
SETTINGS = ("settings.toml", "settings.local.toml")
OWNER = ("owner.json", "workspaces.json", "machine.toml")

type Stamp = tuple[str, int, int, int]


class ViewStamp(msgspec.Struct, frozen=True):
    """The workspace version and the changes only an open stream compares."""

    version: str
    watched: str

    @property
    def rendered(self) -> str:
        """The token of the page as drawn, including the selected task's files."""
        return f"{self.version}.{self.watched}" if self.watched else self.version

    def with_live(self, revision: str) -> ViewStamp:
        """Account for the terminal and base tree alongside the file stamps."""
        if not revision:
            return self
        version = digest((), f"{self.version}:{revision}")
        return ViewStamp(version=version, watched=self.watched)


def stamped(path: Path) -> Stamp | None:
    """A file's name, inode, size and change time."""
    with contextlib.suppress(FileNotFoundError, NotADirectoryError):
        facts = path.lstat()
        return (str(path), facts.st_ino, facts.st_size, facts.st_mtime_ns)
    return None


def files(state: Path, home: Path) -> Iterable[Path]:
    """The files shared by the pages of this workspace."""
    yield from state.glob(RECORDS)
    for pattern in SHARED:
        yield from state.glob(pattern)
    for name in SETTINGS:
        yield state.parent / name
    for name in OWNER:
        yield home / name
    yield from (state.parent.parent / "docs" / "backlog").glob("*.md")


def task_files(state: Path, slug: str | None) -> Iterable[Path]:
    """The additional files watched when a task is open."""
    if slug and SLUG.fullmatch(slug):
        task = state / "tasks" / slug
        if not task.is_symlink():
            yield from task.rglob("*")


def digest(paths: Iterable[Path], revision: str = "") -> str:
    """A version of the files and the results of the owner's acts."""
    found = sorted(filter(None, map(stamped, paths)))
    shown = repr((found, revision))
    return hashlib.sha256(shown.encode()).hexdigest()[:DIGITS]


def look(
    state: Path, home: Path, task: str | None = None, revision: str = ""
) -> ViewStamp:
    """The workspace event ID and the stamp of its open task."""
    return ViewStamp(
        version=digest(files(state, home), revision),
        watched=digest(task_files(state, task)) if task else "",
    )
