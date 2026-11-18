"""Where Lem keeps one repository's state: `.lem/state/` of its main checkout.

Every script that reads or writes Lem's state asks `folder()` for its place, and nothing else
names it. The state is the tasks, the event log, the board's files, the watch's last look at the
forge, the landing lock, the correction queue with its log and claims, and the question gate's log.

The main checkout is the first worktree git lists, where the settings are read from too. A task's
builder runs in a worktree of its own and still writes its state there: a worktree's removal does
not take it, and a session that replaces another finds it. Git never tracks it: the folder holds a
`.gitignore` of `*`, which hides the folder and itself, as the worktrees folder does, in a
repository onboarded before this place too, with no change to a file git tracks.

Lem kept its state in the git directory before (`.git/lem/`). Codex's sandbox keeps `.git`
read-only, so an agent there could not write it. The first script that finds `.git/lem/` and no
`.lem/state/` moves it here, whole: one rename on one volume, or a copy and then the removal of
the old folder when the two are on two volumes. The script says so in one line on stderr. When
both folders exist, nothing is merged: the script refuses, with the two folders named.

This file loads under an old `python3` too, so that the correction hook, which imports it, can
stay silent there.
"""

from __future__ import annotations

import errno
import os
import shutil
import subprocess
import sys
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


def say_on_stderr(line: str) -> None:
    print(f"{Path(sys.argv[0]).name}: {line}", file=sys.stderr)


def move(old: Path, new: Path) -> str:
    """Move the older state folder to its place: how it went, in words, or "" when another process moved it first."""
    try:
        os.rename(old, new)
        return "renamed"
    except FileNotFoundError:
        # another script moved it a moment ago
        return ""
    except OSError as error:
        if error.errno in (errno.ENOTEMPTY, errno.EEXIST) and not old.exists():
            return ""
        if error.errno != errno.EXDEV:
            raise StateError(f"Lem's state could not be moved from {old} to {new} ({error.strerror}); move the folder by hand, then run this again") from error
    # Two volumes: a whole copy under another name first, so that no half of it ever stands in the
    # new place, then the rename, then the old folder goes.
    staging = new.with_name(f"{new.name}.moving-{os.getpid()}")
    try:
        shutil.copytree(old, staging, symlinks=True)
        os.rename(staging, new)
        shutil.rmtree(old)
    except OSError as error:
        shutil.rmtree(staging, ignore_errors=True)
        raise StateError(f"Lem's state could not be copied from {old} to {new} ({error}); copy the folder by hand, remove {old}, then run this again") from error
    return "copied, then removed, since the two are on two volumes"


def folder(start: Path, say=say_on_stderr, timeout: float | None = None) -> Path:
    """The state folder of the repository `start` is in, made when it is absent, with the older
    `.git/lem/` moved there first. `say` gets the one line that tells of a move."""
    main = main_checkout(start, timeout)
    new = main / STATE
    common = git(start, ["rev-parse", "--git-common-dir"], timeout)
    if common is None or not common.strip():
        raise StateError(f"git names no directory of the repository for {start}")
    old = (Path(start) / common.strip()).resolve() / "lem"
    # `new` is looked at first: a script that moves the folder between the two looks makes the
    # second find nothing old, never two folders
    had_new = new.exists()
    if old.is_dir() and not old.is_symlink():
        if had_new:
            raise StateError(
                f"Lem's state is in two folders, {old} (where Lem kept it before) and {new}, and two are never merged: "
                f"keep the one that holds the tasks you want (compare the folders `tasks` in each), remove the other, then run this again",
            )
        new.parent.mkdir(parents=True, exist_ok=True)
        how = move(old, new)
        if how:
            say(f"moved Lem's state from {old} to {new} ({how}); nothing reads {old} any more")
    new.mkdir(parents=True, exist_ok=True)
    ignore = new / ".gitignore"
    if not ignore.is_file():
        ignore.write_text(IGNORE, encoding="utf-8")
    return new
