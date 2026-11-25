"""The files whose stamps a board's stream reads."""

import contextlib
import hashlib
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from starlette.requests import Request

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
RECORDS = "tasks/*/task.json"
DIGITS = 16
SHARED = ("demo", "forge.json", "inbox.json", "backlog/*.md", "tasks/*/sessions.jsonl")
SETTINGS = ("settings.toml", "settings.local.toml")
OWNER = ("owner.json", "workspaces.json", "machine.toml")

type Stamp = tuple[str, int, int, int]


def stamped(path: Path) -> Stamp | None:
    """A file's name, inode, size and change time."""
    with contextlib.suppress(FileNotFoundError, NotADirectoryError):
        facts = path.lstat()
        return (str(path), facts.st_ino, facts.st_size, facts.st_mtime_ns)
    return None


def files(state: Path, home: Path, slug: str | None) -> Iterable[Path]:
    """The board's common files and the files of the one open task."""
    for pattern in SHARED:
        yield from state.glob(pattern)
    for name in SETTINGS:
        yield state.parent / name
    for name in OWNER:
        yield home / name
    yield from (state.parent.parent / "docs" / "backlog").glob("*.md")
    if slug and SLUG.fullmatch(slug):
        task = state / "tasks" / slug
        if not task.is_symlink():
            yield from task.rglob("*")


def digest(paths: Iterable[Path]) -> str:
    """A version that changes when a file is replaced, edited or removed."""
    found = sorted(filter(None, map(stamped, paths)))
    return hashlib.sha256(repr(found).encode()).hexdigest()[:DIGITS]


def shown(request: Request, state: Path) -> str:
    """Read all the stamps that can change the view under this address."""
    home = request.app.state.home
    slug = request.path_params.get("slug") or request.query_params.get("task")
    records = state.glob(RECORDS)
    return digest((*records, *files(state, home, slug)))
