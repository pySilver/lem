"""The `Git` port's facts of paths (the design's part 4): the files of a folder at a commit, the
paths a range changed, and the commits of a branch that a base holds already by their patch.

A path is shown as the `git` adapter shows every name (`adapters/git_cli_names.py`): one line,
each path once.
"""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git_facts import Commit


class GitChanges(Protocol):
    """The files under `folder` at `rev` (`git ls-tree`), the paths that differ between two
    commits with no rename folded (`git diff --name-only --no-renames -z`), and the commits of
    `tip` that `onto` lacks but whose patch it holds (`git log --cherry-mark`), which a rebase
    onto it leaves out."""

    def files(self, where: Path, rev: str, folder: str) -> tuple[str, ...]: ...
    def changed_paths(self, where: Path, since: str, until: str) -> tuple[str, ...]: ...
    def left_out(self, where: Path, onto: str, tip: str) -> tuple[Commit, ...]: ...
