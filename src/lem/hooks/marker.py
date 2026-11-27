"""The marker of a folder this Lem made, read and written as `kernel.folders` does, with `os` alone.

A state folder or a home folder that holds `lem-state.json` is this Lem's. One that holds anything
else and no marker holds the files of Lem 0.3: a hook writes nothing into it and reads nothing of
it. A hook that writes marks an absent or empty folder first, with the same bytes as the first
write of a command (`notes/core.md`, "The hooks' look at the marker").
"""

import io
import os

from lem.hooks import raw, where

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

FORM = b'{"form": 1}\n'
# What a state folder may hold and still count as empty: git's ignore file, which `lem init`
# writes before any state.
STATE_EMPTY = frozenset((".gitignore",))
# A marker is made only where none is, and never through a link.
OWNER_FOLDER = 0o700
CREATE = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW


def home_of(environ: Mapping[str, str]) -> str | None:
    """Lem's home folder, by the rule of `kernel.paths.home`; None for a relative
    XDG_CONFIG_HOME, which each folder would read as another place."""
    named = environ.get("XDG_CONFIG_HOME", "")
    if not named:
        return f"{environ.get('HOME', '')}/.config/lem"
    return f"{named}/lem" if named.startswith("/") else None


def own_folder(parent: str, name: str) -> str:
    """The folder `name` in `parent`, made for the owner alone when it is not there; OSError
    when it is a link or no folder, so that no file of the hook lands in another place."""
    import stat
    from pathlib import Path

    path = f"{parent}/{name}"
    Path(path).mkdir(mode=OWNER_FOLDER, exist_ok=True)
    if not stat.S_ISDIR(os.lstat(path).st_mode):
        raise NotADirectoryError(f"{path} is a link or no folder")
    return path


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
