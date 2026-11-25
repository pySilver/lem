"""The backlog folder of a task's worktree, read through git: its items at the tip, the files it
had at the base, and the items the branch adds (`land.items_at`, `land.base_items` and
`land.items_added` on `main`).

The tip is the worktree's commit, and the worktree is clean when a step reads it, so the files
on disk are the tip's; each is read from git, so an untracked file is no item of it. The base's
files are the tip's and those the change removes or edits, each that git has at the base.
"""

from typing import TYPE_CHECKING

from lem.model.landing import items
from lem.model.landing.filing_place import Shelf

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git

# The backlog folder, relative to the root of the repository: its one place (`land.backlog_of`
# on `main`).
FOLDER = "docs/backlog"


def on_disk(worktree: Path) -> tuple[str, ...]:
    """The files under the worktree's backlog folder, as paths from the repository's root."""
    folder = worktree / FOLDER
    if not folder.is_dir():
        return ()
    found = (path for path in folder.rglob("*") if path.is_file())
    return tuple(sorted(path.relative_to(worktree).as_posix() for path in found))


def read_at(git: Git, worktree: Path, rev: str, path: str) -> items.BacklogItem | None:
    """The item at `path` as `rev` has it; None for a file that is no item or not there."""
    found = git.show(worktree, rev, path)
    if found is None:
        return None
    return items.read(path, found.decode("utf-8", errors="replace"))


def at_tip(git: Git, worktree: Path, tip: str) -> tuple[items.BacklogItem, ...]:
    """Each item of the backlog folder at the tip."""
    read = (read_at(git, worktree, tip, path) for path in on_disk(worktree))
    return tuple(found for found in read if found is not None)


def files_at_base(git: Git, worktree: Path, base: str, tip: str) -> frozenset[str]:
    """Each file of the backlog folder at the base: the tip's, and those the change touched,
    that git has at the base."""
    changed = git.diff_stat(worktree, base, tip).paths
    folder = f"{FOLDER}/"
    candidates = {
        *on_disk(worktree),
        *(path for path in changed if path.startswith(folder)),
    }
    return frozenset(
        path for path in candidates if git.show(worktree, base, path) is not None
    )


def at_base(
    git: Git, worktree: Path, base: str, tip: str
) -> tuple[items.BacklogItem, ...]:
    """Each item of the backlog folder at the base, for the reviewer, who names in `open` the
    one that holds a defect it sees."""
    paths = sorted(files_at_base(git, worktree, base, tip))
    read = (read_at(git, worktree, base, path) for path in paths)
    return tuple(found for found in read if found is not None)


def added(
    git: Git, worktree: Path, base: str, tip: str
) -> tuple[items.BacklogItem, ...]:
    """Each item the branch adds to the backlog folder: at the tip, and not at the base."""
    there = files_at_base(git, worktree, base, tip)
    return tuple(
        found for found in at_tip(git, worktree, tip) if found.path not in there
    )


def shelf(git: Git, worktree: Path, tip: str) -> Shelf:
    """The backlog folder at the tip, as `file` places a defect in it: every file in the
    worktree's folder, and each item."""
    paths = frozenset(on_disk(worktree))
    return Shelf(folder=FOLDER, paths=paths, shelved=at_tip(git, worktree, tip))
