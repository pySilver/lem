"""A folder of the state folder walked whole: its newest write, and its removal with all it
holds, with no link followed."""

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from lem.store.retention.files import emptied, rmdir

if TYPE_CHECKING:
    from lem.store.retention.files import Removal

# One folder of a walk: its path, its folders and its files.
type Walked = tuple[str, list[str], list[str]]


def newest_write(entry: Path) -> datetime:
    """The newest moment of a write to `entry` or to anything in it."""
    newest = entry.lstat().st_mtime
    for at, inner, names in os.walk(entry):
        for name in (*inner, *names):
            newest = max(newest, (Path(at) / name).lstat().st_mtime)
    return datetime.fromtimestamp(newest, tz=UTC).replace(microsecond=0)


def files_in(removal: Removal, folder: Path) -> list[Path]:
    """Every file under `folder`; each link to a folder, which the walk does not follow, is
    named among what was skipped."""
    found: list[Path] = []
    for walked in os.walk(folder):
        found.extend(listed(removal, walked))
    return found


def listed(removal: Removal, walked: Walked) -> list[Path]:
    """The files of one folder of a walk; its links to folders are named."""
    at, inner, names = walked
    for linked in inner:
        removal.link(Path(at) / linked)
    return [Path(at) / name for name in names]


def tree(removal: Removal, path: Path) -> int:
    """Remove a file, or a folder with all it holds, deepest first; the bytes removed. A link
    inside stays, and so does the folder that holds it."""
    if not path.is_dir():
        return removal.removed(path) or 0
    sizes = [removal.removed(one) for one in files_in(removal, path)]
    emptied(removal, path)
    if not removal.dry:
        rmdir(removal, path)
    return sum(size or 0 for size in sizes)
