"""The backlog folder of a task's worktree, read through git: its items at the tip, the files it
had at the base, and the items the branch adds (`land.items_at`, `land.base_items` and
`land.items_added` on `main`). Only a file git has at the tip is one of its files; a file
on disk that git does not track takes its name and holds no defect.

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


def files_at_base(
    git: Git, worktree: Path, base: str, changed: tuple[str, ...]
) -> frozenset[str]:
    """Each file of the backlog folder at the base: the tip's, and those the change touched
    (`changed`, the diff's paths), that git has at the base."""
    folder = f"{FOLDER}/"
    candidates = {
        *on_disk(worktree),
        *(path for path in changed if path.startswith(folder)),
    }
    return frozenset(
        path for path in candidates if git.show(worktree, base, path) is not None
    )


def at_base(
    git: Git, worktree: Path, base: str, there: frozenset[str]
) -> tuple[items.BacklogItem, ...]:
    """Each item of the backlog folder at the base, whose files are `there`, for the
    reviewer, who names in `open` the one that holds a defect it sees."""
    read = (read_at(git, worktree, base, path) for path in sorted(there))
    return tuple(found for found in read if found is not None)


def added(
    git: Git, worktree: Path, tip: str, there: frozenset[str]
) -> tuple[items.BacklogItem, ...]:
    """Each item the branch adds to the backlog folder: at the tip, and not among the base's
    files `there`."""
    return tuple(
        found for found in at_tip(git, worktree, tip) if found.path not in there
    )


def shelf(git: Git, worktree: Path, tip: str) -> Shelf:
    """The backlog folder at the tip, as `file` places a defect in it: the files git has
    there, each item, and every name taken on disk."""
    disk = frozenset(on_disk(worktree))
    tracked = (path for path in disk if git.show(worktree, tip, path) is not None)
    return Shelf(
        folder=FOLDER,
        paths=frozenset(tracked),
        shelved=at_tip(git, worktree, tip),
        taken=disk,
    )
