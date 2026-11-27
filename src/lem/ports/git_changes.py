"""The `Git` port's facts of paths (the design's part 4): the files of a folder at a commit, the
paths a range changed, the commits of a branch that a base holds already by their patch, and
what a merge commit changed beside git's own merge of its parents.

The names are filesystem paths, ready for another call that names a file.
"""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git_facts import Commit


class GitChanges(Protocol):
    """The files under `folder` at `rev` (`git ls-tree`), the paths that differ between two
    commits with no rename folded (`git diff --name-only --no-renames -z`), and the commits of
    `tip` that `onto` lacks but whose patch it holds (`git log --cherry-mark`), which a rebase
    onto it leaves out; and the diff of a merge commit against git's own merge of its parents
    (`git show --remerge-diff`), empty for a merge git made alone, whose form "is subject to
    change" (git-show, 2026-11-27)."""

    def files(self, where: Path, rev: str, folder: str) -> tuple[str, ...]: ...
    def changed_paths(self, where: Path, since: str, until: str) -> tuple[str, ...]: ...
    def left_out(self, where: Path, onto: str, tip: str) -> tuple[Commit, ...]: ...
    def remerge(self, where: Path, commit: str) -> str: ...
