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
    """The main checkout of the repository `folder` is in, or None outside one."""
    here = os.path.realpath(folder)
    while not os.access(f"{here}/.git", os.F_OK):
        if here == "/":
            return None
        here = parent(here)
    return parent(common_dir(f"{here}/.git"))


def folder_of(found: raw.Event, environ: Mapping[str, str]) -> str:
    """The folder the session runs in: the event's, else Claude Code's project, else this
    process's own."""
    project = environ.get("CLAUDE_PROJECT_DIR")
    return raw.text(found, "cwd") or project or "."


def task_folder(found: raw.Event, environ: Mapping[str, str]) -> str | None:
    """The folder of the session's task in the state of its main checkout, or None for a
    session that is no task's, or whose task has no folder there."""
    slug = slug_of(environ)
    if slug is None:
        return None
    checkout = checkout_of(folder_of(found, environ))
    folder = f"{checkout}/{STATE}/tasks/{slug}"
    return folder if checkout and raw.is_folder(folder) else None
