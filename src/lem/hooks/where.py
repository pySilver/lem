"""Where a hook's files are: the main checkout of the folder a session runs in, and the folder of
the session's task in its state.

The main checkout is found as `store.places.workspace` finds it, from the files git keeps
(`.git`, `gitdir`, `commondir`), with no git started: a task's session runs in the main checkout
and its builders in the task's worktree, and both reach the one state folder.
"""

import os

from lem.hooks import raw

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

STATE = ".lem/state"
# The marker of a state folder this Lem made (`kernel.folders.MARKER`). A state folder without
# it holds the files of Lem 0.3, which no hook of this Lem writes into or reads.
MARKER = "lem-state.json"
# The letters of a task's name, as `store.places.SLUG` holds them.
SLUG_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")


def slug_of(environ: Mapping[str, str]) -> str | None:
    """`LEM_TASK`, which `lem session open` puts on the launch line, when it is a task's name:
    lower-case words and digits joined by hyphens."""
    slug = environ.get("LEM_TASK", "").strip()
    if slug and set(slug) <= SLUG_LETTERS and all(slug.split("-")):
        return slug
    return None


def parent(path: str) -> str:
    """The folder that holds `path`, and `/` for the root."""
    above = path.rpartition("/")[0]
    return above or "/"


def resolved(base: str, named: str) -> str:
    """The real path of `named`, read from the folder `base` when it is relative."""
    whole = named if named.startswith("/") else f"{base}/{named}"
    return os.path.realpath(whole)


def common_dir(dot_git: str) -> str:
    """The git folder that the checkout of `dot_git` shares with every worktree; OSError when
    a file of git does not read."""
    if raw.is_folder(dot_git):
        return dot_git
    named = raw.read_bytes(dot_git).decode().strip().removeprefix("gitdir:")
    own = resolved(parent(dot_git), named.strip())
    try:
        shared = raw.read_bytes(f"{own}/commondir").decode()
    except OSError:
        return own
    return resolved(own, shared.strip())


def checkout_of(folder: str) -> str | None:
    """The main checkout of the repository `folder` is in, or None outside one and for a
    folder that is not there (a worktree that was removed)."""
    if not raw.is_folder(folder):
        return None
    here = os.path.realpath(folder)
    while not os.access(f"{here}/.git", os.F_OK):
        if here == "/":
            return None
        here = parent(here)
    return parent(common_dir(f"{here}/.git"))


def checkout_here(found: raw.Event, environ: Mapping[str, str]) -> str | None:
    """The main checkout of the folder the session runs in (the event's, else Claude Code's
    project, else this process's own) when its state folder is one this Lem made, with the
    marker; None outside a repository, and for a state folder of Lem 0.3."""
    project = environ.get("CLAUDE_PROJECT_DIR")
    checkout = checkout_of(raw.text(found, "cwd") or project or ".")
    marker = f"{checkout}/{STATE}/{MARKER}"
    return checkout if checkout and os.access(marker, os.F_OK) else None


def task_folder(found: raw.Event, environ: Mapping[str, str]) -> str | None:
    """The folder of the session's task in the state of its main checkout, or None for a
    session that is no task's, whose task has no folder there, whose folder a link puts in
    another place, or whose state folder is Lem 0.3's: a hook touches no file of another
    checkout, nor of the Lem before."""
    slug = slug_of(environ)
    if slug is None:
        return None
    checkout = checkout_here(found, environ)
    if checkout is None:
        return None
    folder = f"{checkout}/{STATE}/tasks/{slug}"
    if not raw.is_folder(folder):
        return None
    return folder if os.path.realpath(folder) == folder else None
