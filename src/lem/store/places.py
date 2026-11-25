"""Where a workspace is, and where it keeps Lem's state: `.lem/state/` of its main checkout,
which git never sees, a folder for each task, and the shared locks (the design's part 3,
"Elsewhere").

`workspace(folder)` turns the folder a call starts from (`lem --repo PATH`, else the working
one: `cli/place.py`) into the workspace: the main checkout, from a task's worktree too, which is
the first worktree git lists, read from the files git keeps (`.git`, `gitdir`, `commondir`) with
no git started, since every command reads it.

The folder holds a `.gitignore` of `*`, which hides the folder and itself with no change to a
file git tracks. A slug is a folder's name, so it is lower-case words and digits joined by
hyphens, and anything else is refused before a path is made of it.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from lem.kernel import folders
from lem.kernel.errors import Refusal
from lem.store import guard

STATE = Path(".lem") / "state"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def state_of(checkout: Path) -> Path:
    """The state folder of the main checkout `checkout`, made with its ignore file and its
    marker when it is not there; refused when it holds the state of the Lem before."""
    state = checkout / STATE
    guard.writable(state)
    return state


def task_folder(state: Path, slug: str) -> Path:
    """The folder of the task `slug` in `state`; a slug that is no such name is refused."""
    if not SLUG.fullmatch(slug):
        raise Refusal(
            "slug",
            f"{slug!r} is no task's name",
            "name a task by lower-case words and digits joined by hyphens: fix-the-login",
        )
    return state / "tasks" / slug


def locks_folder(state: Path) -> Path:
    """The folder of the workspace's shared locks (the claim, the merge, the serial checks),
    made when it is not there."""
    folder = state / "locks"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


@dataclass(frozen=True, kw_only=True, slots=True)
class Workspace:
    """A workspace: its main checkout, its `.lem/`, and its state folder."""

    checkout: Path
    lem: Path
    state: Path


def common_dir(dot_git: Path) -> Path:
    """The git directory a checkout's `.git` shares with every worktree of its repository."""
    if dot_git.is_dir():
        return dot_git
    named = dot_git.read_text(encoding="utf-8").strip().removeprefix("gitdir:").strip()
    own = (dot_git.parent / named).resolve()
    shared = own / "commondir"
    if not shared.is_file():
        return own
    return (own / shared.read_text(encoding="utf-8").strip()).resolve()


def checkout_of(folder: Path) -> Path:
    """The main checkout of the repository `folder` is in, from a task's worktree too, where
    Lem need not be set up yet (`lem init` starts there); refused outside a repository."""
    start = folder.resolve()
    marks = (above / ".git" for above in (start, *start.parents))
    found = next((mark for mark in marks if mark.exists()), None)
    if found is None:
        raise Refusal(
            "no-repository",
            f"{start} is in no git repository",
            "run it inside a repository's checkout, or name one with lem --repo PATH",
        )
    checkout = common_dir(found).parent
    folders.inside_test_root(checkout)
    return checkout


def workspace(folder: Path) -> Workspace:
    """The workspace `folder` is in; refused when it is in no repository, in one where Lem is
    not set up, or in one that holds the state of the Lem before."""
    checkout = checkout_of(folder)
    if not (checkout / ".lem").is_dir():
        raise Refusal(
            "no-lem",
            f"Lem is not set up in {checkout}: it has no .lem folder",
            "lem init --base BRANCH sets it up, or lem --repo PATH names another repository",
        )
    guard.readable(checkout / STATE)
    return Workspace(checkout=checkout, lem=checkout / ".lem", state=checkout / STATE)
