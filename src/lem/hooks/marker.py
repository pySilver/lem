"""The marker of a folder this Lem made, read and written as `kernel.folders` does, with `os` alone.

A state folder or a home folder that holds `lem-state.json` is this Lem's. One that holds anything
else and no marker holds the files of Lem 0.3: a hook writes nothing into it and reads nothing of
it. A hook that writes marks an absent or empty folder first, with the same bytes as the first
write of a command (`notes/core.md`, "The hooks' look at the marker").
"""

import io
import os

from lem.hooks import raw, where

FORM = b'{"form": 1}\n'
# What a state folder may hold and still count as empty: git's ignore file, which `lem init`
# writes before any state.
STATE_EMPTY = frozenset((".gitignore",))
# A marker is made only where none is, and never through a link.
CREATE = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW


def has(folder: str) -> bool:
    """Whether `folder` holds the marker of this Lem."""
    return os.access(f"{folder}/{where.MARKER}", os.F_OK)


def ours(folder: str, empty: frozenset[str]) -> bool:
    """Whether this Lem may write into `folder`: it holds the marker, or it is absent or holds
    only the names `empty`, and is marked now. False for a folder of the Lem before; OSError when
    the folder cannot be made or marked."""
    if has(folder):
        return True
    try:
        with os.scandir(folder) as entries:
            held = {entry.name for entry in entries}
    except FileNotFoundError:
        from pathlib import Path

        held = set()
        Path(folder).mkdir(parents=True, exist_ok=True)
    if not held <= empty:
        return False
    try:
        descriptor = os.open(f"{folder}/{where.MARKER}", CREATE, raw.MODE)
    except FileExistsError:
        # another writer marked it first, with the same bytes
        return True
    with io.FileIO(descriptor, "w") as stream:
        stream.write(FORM)
    return True
