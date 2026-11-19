"""Where Lem keeps one repository's state: `.lem/state/` of its main checkout.

Every script that reads or writes Lem's state asks `folder()` for its place, and nothing else
names it. The state is the tasks, the event log, the board's files, the watch's last look at the
forge, the landing lock, and the correction queue with its log and claims.

The main checkout is the first worktree git lists, where the settings are read from too. A task's
builder runs in a worktree of its own and still writes its state there: a worktree's removal does
not take it, and a session that replaces another finds it. Git never tracks it: the folder holds a
`.gitignore` of `*`, which hides the folder and itself, as the worktrees folder does, with no change
to a file git tracks. It is not in the git directory, because Codex's sandbox keeps `.git` read-only.

One fact is the machine's and not a repository's: whether the owner is there or away. Its one place
is `owner_mark()`, `owner.jsonl` in `config()`, a folder in the home directory, the one Lem keeps
there. A read never makes that folder: only the write of the owner's status does, and nothing else
of Lem's goes into it.

This file loads under an old `python3` too, so that the correction hook, which imports it, can
stay silent there.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

STATE = Path(".lem") / "state"
# what the folder's own ignore file says: everything in it, and the file itself
IGNORE = "*\n"


class StateError(Exception):
    pass


def git(start: Path, args: list, timeout: float | None) -> str | None:
    try:
        ran = subprocess.run(["git", "-C", str(start), *args], capture_output=True, text=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return ran.stdout if ran.returncode == 0 else None


# The main checkout of each folder this process found one for. It cannot change while one command
# runs, and a command that calls its siblings in its own process asks for it many times, so git is
# asked once for each folder. Only the path is kept: the list of worktrees, which a command may
# change, is asked again each time. A process that runs many commands calls `forget()` between two.
CHECKOUTS = {}


def forget() -> None:
    CHECKOUTS.clear()


def main_checkout(start: Path, timeout: float | None = None) -> Path:
    """The checkout every worktree hangs off: the first entry `git worktree list` gives."""
    key = os.path.abspath(start)
    if key in CHECKOUTS:
        return CHECKOUTS[key]
    # -z ends each field with a NUL: a path may hold a line break, and a split on lines would cut it
    listed = git(start, ["worktree", "list", "--porcelain", "-z"], timeout)
    first = next((field[len("worktree "):] for field in (listed or "").split("\0") if field.startswith("worktree ")), None)
    if not first:
        raise StateError(f"git lists no worktree for {start}: Lem's state belongs to a repository, so run this inside its checkout")
    CHECKOUTS[key] = Path(first)
    return CHECKOUTS[key]


def config() -> Path:
    """Lem's folder in the home directory: `$XDG_CONFIG_HOME/lem` when that variable is set and not
    empty, else `~/.config/lem`. Nothing here makes it."""
    named = os.environ.get("XDG_CONFIG_HOME", "")
    if not named:
        return Path.home() / ".config" / "lem"
    if not os.path.isabs(named):
        # a relative path would be read from the folder each command starts in, so two repositories would read two marks
        raise StateError(f"XDG_CONFIG_HOME is {named!r}, a relative path: Lem keeps the owner's status under it for every repository, so set it to an absolute path, or unset it for ~/.config")
    return Path(named) / "lem"


# The owner's status, the machine's: one line for each away and back he said, appended (`project.py owner`).
OWNER_MARK = "owner.jsonl"


def owner_mark() -> Path:
    """The file of the owner's status, which every repository on this machine reads; it may not exist."""
    return config() / OWNER_MARK


def folder(start: Path, timeout: float | None = None) -> Path:
    """The state folder of the repository `start` is in, made when it is absent."""
    new = main_checkout(start, timeout) / STATE
    new.mkdir(parents=True, exist_ok=True)
    ignore = new / ".gitignore"
    if not ignore.is_file():
        ignore.write_text(IGNORE, encoding="utf-8")
    return new
