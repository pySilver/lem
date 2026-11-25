"""The tree the checks judge, and the tree they leave (`land.stale_bytecode`, `remove_bytecode`
and `remove_left` on `main`; the owner's ruling "The checks remove what their own commands
leave", 2026-11-17).

Before the first command each ignored `__pycache__` with no ignored folder above it goes
(`model/landing/checks_bytecode.py`). After the last, each file the commands wrote that git
neither tracks nor ignores goes, with the folders it leaves empty, red, green or stopped, so that
the next step finds the worktree clean; a file that was there before the run stays. The worktree
is the task's own, made by Lem.
"""

import shutil
from typing import TYPE_CHECKING

from lem.app.landing import checks_git
from lem.kernel.errors import Refusal
from lem.model.landing import checks_bytecode

if TYPE_CHECKING:
    from pathlib import Path


def stale(worktree: Path) -> tuple[str, ...]:
    """Each ignored `__pycache__` of the worktree with no ignored folder above it, as git
    names it."""
    listed = checks_git.ignored(worktree)
    above = checks_bytecode.folders_above(checks_bytecode.candidates(listed))
    ignored = checks_git.ignored_of(worktree, above) if above else frozenset()
    return checks_bytecode.stale(listed, ignored)


def removed(worktree: Path, folder: str, slug: str) -> None:
    """Remove one ignored `__pycache__` folder whole. A link, or what is no folder when the
    removal comes to it, stays, and so does a folder whose parent resolves outside the
    worktree; a link inside it is removed as a link, never followed. A folder that cannot go
    refuses the run."""
    root = worktree.resolve()
    path = root / folder.rstrip("/")
    if path.is_symlink() or not path.is_dir():
        return
    if not path.parent.resolve().is_relative_to(root):
        return
    try:
        shutil.rmtree(path)
    except OSError as error:
        raise Refusal(
            "bytecode-folder",
            f"the checks cannot remove the ignored {path} that was there before them "
            f"({error})",
            f"remove it, then run `lem land checks {slug}` again",
        ) from None


def cleared(worktree: Path, slug: str) -> tuple[str, ...]:
    """Remove the stale bytecode before the first command, and name each folder that went."""
    found = stale(worktree)
    for folder in found:
        removed(worktree, folder, slug)
    return found


def left(worktree: Path, path: str) -> None:
    """Remove one file a command left untracked, and each folder above it that it leaves
    empty, up to the worktree's root. A link is removed as a link, never followed; git lists
    no file under a linked folder, so the folder that holds it is inside the worktree."""
    root = worktree.resolve()
    gone = root / path
    if not gone.parent.resolve().is_relative_to(root):
        return
    gone.unlink(missing_ok=True)
    folder = gone.parent
    while folder != root and folder.is_relative_to(root):
        try:
            folder.rmdir()
        except OSError:
            return
        folder = folder.parent


def swept(worktree: Path, before: tuple[str, ...]) -> tuple[str, ...]:
    """Remove what the commands left that git neither tracks nor ignores and that was not
    there before the run (`before`), and name each file."""
    now = set(checks_git.untracked(worktree))
    found = tuple(sorted(now - set(before)))
    for path in found:
        left(worktree, path)
    return found
