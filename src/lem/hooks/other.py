"""Another `lem` first on the PATH: the line that names it, read by its real path, never run.

A session's commands run the first `lem` on its PATH. When that is another file than the app
whose hook runs (an old install, a checkout's), the session's `lem` lines reach a Lem of another
version; `session-start` says so to the owner, with the folder that must come first: the folder
of the search path that holds the app's own `lem`, else the folder an installer links `lem` into
(Homebrew's `bin` of the prefix that holds the app's keg, uv's `~/.local/bin`), never the app's
own `bin`, which holds its Python and changes its name with each Homebrew update.
"""

import os
import sys

from lem.hooks import where

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

# The part of a path that names a Homebrew keg of Lem: `PREFIX/Cellar/lem/VERSION/...`.
KEG = "/Cellar/lem/"


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


def other_lem(environ: Mapping[str, str], own: str) -> str | None:
    """The line that says the first `lem` on the search path of `environ` is another file than
    `own`, the app's command; None when no `lem` is on it, when it is `own`, or when `own` is
    not there."""
    folders = [folder for folder in environ.get("PATH", "").split(":") if folder]
    commands = (f"{folder}/lem" for folder in folders)
    first = next((path for path in commands if runnable(path)), None)
    if first is None or not runnable(own) or same(first, own):
        return None
    return line(first, own, [*folders, *link_folders(own, environ)])


def link_folders(own: str, environ: Mapping[str, str]) -> tuple[str, ...]:
    """The folders an installer links the command `own` into: Homebrew's `bin` when `own` is in
    a keg, and uv's tool folder (`XDG_BIN_HOME`, else `~/.local/bin`)."""
    prefix, keg, _ = os.path.realpath(own).partition(KEG)
    brew = (f"{prefix}/bin",) if keg else ()
    uv = environ.get("XDG_BIN_HOME") or f"{environ.get('HOME', '')}/.local/bin"
    return (*brew, uv)


def line(first: str, own: str, folders: list[str]) -> str:
    """The line for `first`, another `lem` than `own`, with the first folder of `folders` that
    holds `own` to put before its folder; with no such folder, Homebrew's `bin` and the link
    that puts `own` there for a keg, else the folder of `own`."""
    theirs = where.parent(first)
    said = f"lem: {first} comes first on PATH, and it is not Lem's command {own}; the owner"
    holding = (folder for folder in folders if same(f"{folder}/lem", own))
    mine = next(holding, None)
    if mine is not None:
        return f"{said} puts {mine} before {theirs} in his PATH"
    keg = os.path.realpath(own).partition(KEG)
    if keg[1]:
        return f"{said} runs `brew link lem` and puts {keg[0]}/bin before {theirs} in his PATH"
    return f"{said} puts {where.parent(own)} before {theirs} in his PATH"
