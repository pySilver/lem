"""The files a call names, each as one path relative to its checkout, however it is named.

The checkout is the one the call starts in, a task's worktree too: a builder names the files of
its own branch, and its rules are the ones its branch holds.
"""

import os
from pathlib import Path

from lem.kernel import folders
from lem.kernel.errors import Refusal

NO_NAMES = ("", ".", "..")


def checkout_of(folder: Path) -> Path:
    """The checkout `folder` is in: the nearest folder up from it that holds `.git`, a
    worktree's own too; refused outside one."""
    start = folder.resolve()
    found = next(filter(holds_git, (start, *start.parents)), None)
    if found is None:
        raise Refusal(
            "no-repository",
            f"{start} is in no git repository",
            "run it inside a repository's checkout, or name one with lem --repo PATH",
        )
    folders.inside_test_root(found)
    return found


def holds_git(folder: Path) -> bool:
    """Whether `folder` is the top of a checkout."""
    return (folder / ".git").exists()


def named(root: Path, given: str) -> str:
    """The file `given` names, relative to `root`, or a path that leaves it refused.

    Its folder is resolved the way the file system reads it, a link first and `..` after it:
    `alias/../x` is beside what `alias` points at. The last name is kept as written, since the
    file may be a link or be gone.
    """
    full = root / given
    if full == root or full.name in NO_NAMES:
        raise Refusal(
            "no-file", f"{given} names no file", "name the files a change touches"
        )
    real = Path(os.path.realpath(full.parent)) / full.name
    if real == root or not real.is_relative_to(root):
        raise Refusal(
            "outside",
            f"{given} is not inside {root}",
            "name the files of this repository",
        )
    return real.relative_to(root).as_posix()
