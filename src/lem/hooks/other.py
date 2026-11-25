"""Another `lem` first on the PATH: the line that names it, read by its real path, never run.

A session's commands run the first `lem` on its PATH. When that is another file than the app
whose hook runs (an old install, a checkout's), the session's `lem` lines reach a Lem of another
version; `session-start` says so to the owner, with the folder that must come first.
"""

import os
import sys

from lem.hooks import where


def own_command() -> str:
    """The app's command `lem`: the one beside the Python that runs this hook."""
    return f"{where.parent(sys.executable)}/lem"


def runnable(path: str) -> bool:
    """Whether `path` is a file this process may run."""
    if not os.access(path, os.X_OK):
        return False
    return not os.access(f"{path}/.", os.F_OK)


def identity(path: str) -> tuple[int, int] | None:
    """The device and inode of the file `path` names, after its links; None when it is not
    there."""
    try:
        found = os.lstat(os.path.realpath(path))
    except OSError:
        return None
    return (found.st_dev, found.st_ino)


def same(one: str, other: str) -> bool:
    """Whether the two paths are one file, after their links, a hard link too."""
    first = identity(one)
    return first is not None and first == identity(other)


def other_lem(search: str, own: str) -> str | None:
    """The line that says the first `lem` on the search path `search` is another file than
    `own`, the app's command; None when no `lem` is on it, when it is `own`, or when `own` is
    not there."""
    folders = [folder for folder in search.split(":") if folder]
    commands = (f"{folder}/lem" for folder in folders)
    first = next((path for path in commands if runnable(path)), None)
    if first is None or not runnable(own) or same(first, own):
        return None
    return line(first, own, folders)


def line(first: str, own: str, folders: list[str]) -> str:
    """The line for `first`, another `lem` than `own`, with the folder of `folders` that must
    come before its folder."""
    mine = (folder for folder in folders if same(f"{folder}/lem", own))
    before = next(mine, where.parent(own))
    theirs = where.parent(first)
    return (
        f"lem: {first} comes first on PATH, and it is not Lem's command {own}; "
        f"the owner puts {before} before {theirs} in his PATH"
    )
