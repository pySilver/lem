"""The `Git` port: the facts the landing reads and the acts it takes (the design's part 4).

Every path is a checkout or a worktree on disk; every commit is a full sha. A fact never
changes the repository. An act that git refuses (a conflict, a hook, a lease) gives its typed
refusal; one that could not run raises `Unanswered`. The port is four parts of seven methods or
fewer, joined in `GitFacts`, `GitActs` and `Git`.
"""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git_facts import Commit, Conflict, DiffStat, GitRefused, RebaseState
    from lem.records.base import Sha


class GitHistory(Protocol):
    """Facts of the commits: a ref's tip and a commit's tree, their ancestry, a range, its size,
    and the tree a merge would make."""

    def tip(self, where: Path, ref: str) -> Sha | None: ...
    def tree(self, where: Path, rev: str) -> Sha: ...
    def merge_base(self, where: Path, first: str, second: str) -> Sha | None: ...
    def is_ancestor(self, where: Path, older: str, newer: str) -> bool: ...
    def commits(self, where: Path, since: str, until: str) -> tuple[Commit, ...]: ...
    def diff_stat(self, where: Path, since: str, until: str) -> DiffStat: ...
    def merge_tree(self, where: Path, base: str, tip: str) -> Sha | Conflict: ...


class GitPlaces(Protocol):
    """Facts of the checkouts: the main one, a worktree's cleanness and rebase, a file at a
    commit, and the remote's branch as last fetched."""

    def main_checkout(self, start: Path) -> Path: ...
    def clean(self, where: Path) -> bool: ...
    def show(self, where: Path, rev: str, path: str) -> bytes | None: ...
    def rebase_state(self, where: Path) -> RebaseState | None: ...
    def remote_head(self, where: Path, branch: str) -> Sha | None: ...


class GitFacts(GitHistory, GitPlaces, Protocol):
    """Every fact, none of which changes the repository."""


class GitRewrite(Protocol):
    """The acts on a task's branch: fetch, rebase and its abort, commit, and a push with a
    lease on the commit Lem pushed last (`landing.md` H 3), None when the branch is new."""

    def fetch(self, where: Path) -> None: ...
    def rebase(
        self, worktree: Path, onto: str, *, reapply: bool
    ) -> Sha | Conflict | GitRefused: ...
    def abort(self, worktree: Path) -> None: ...
    def commit(self, worktree: Path, message: str, paths: tuple[str, ...]) -> Sha: ...
    def push(
        self, worktree: Path, branch: str, expect: Sha | None
    ) -> Sha | GitRefused: ...


class GitBranches(Protocol):
    """The acts on worktrees and branches: add and remove a worktree, delete a branch only at
    the commit named, and fast-forward a checkout."""

    def worktree_add(
        self, checkout: Path, path: Path, branch: str, start: str
    ) -> None: ...
    def worktree_remove(self, checkout: Path, path: Path) -> None: ...
    def branch_delete(self, checkout: Path, branch: str, expect: Sha) -> bool: ...
    def fast_forward(self, checkout: Path, ref: str) -> Sha | GitRefused: ...


class GitActs(GitRewrite, GitBranches, Protocol):
    """Every act."""


class Git(GitFacts, GitActs, Protocol):
    """The whole port."""
