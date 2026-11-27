"""The `Git` port: the facts the landing reads and the acts it takes (the design's part 4).

Every path is a checkout or a worktree on disk; every commit is a full sha. A fact never
changes the repository. An act that git refuses (a conflict, a hook, a lease) gives its typed
refusal; one that could not run raises `Unanswered`. The port is five parts of seven methods or
fewer, joined in `GitFacts`, `GitActs` and `Git`; the paths of a commit and a range
(`ports/git_changes.py`) are a part of `GitHistory`.
"""

from typing import TYPE_CHECKING, Protocol

from lem.ports.git_changes import GitChanges

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git_facts import Commit, Conflict, DiffStat, GitRefused, RebaseState
    from lem.records.base import Sha


class GitHistory(GitChanges, Protocol):
    """Facts of the commits: a ref's tip and a commit's tree, their ancestry, a range, its size,
    and the tree a merge would make; and the paths of a commit and a range (`GitChanges`)."""

    def tip(self, where: Path, ref: str) -> Sha | None: ...
    def tree(self, where: Path, rev: str) -> Sha: ...
    def merge_base(self, where: Path, first: str, second: str) -> Sha | None: ...
    def is_ancestor(self, where: Path, older: str, newer: str) -> bool: ...
    def commits(self, where: Path, since: str, until: str) -> tuple[Commit, ...]: ...
    def diff_stat(self, where: Path, since: str, until: str) -> DiffStat: ...
    def merge_tree(self, where: Path, base: str, tip: str) -> Sha | Conflict: ...


class GitPlaces(Protocol):
    """Facts of the checkouts: the main one, the branch one is on, its cleanness (with its
    untracked files, or of what git tracks only) and its rebase, a file at a commit, the
    remote's branch as last fetched, and origin's address as the checkout's own configuration
    names it."""

    def main_checkout(self, start: Path) -> Path: ...
    def branch_of(self, where: Path) -> str | None: ...
    def clean(self, where: Path, *, untracked: bool = True) -> bool: ...
    def show(self, where: Path, rev: str, path: str) -> bytes | None: ...
    def rebase_state(self, where: Path) -> RebaseState | None: ...
    def remote_head(self, where: Path, branch: str) -> Sha | None: ...
    def origin_url(self, where: Path) -> str | None: ...


class GitFacts(GitHistory, GitPlaces, Protocol):
    """Every fact, none of which changes the repository."""


class GitRewrite(Protocol):
    """The acts on a task's branch: fetch, rebase and its abort, a merge commit of `ref` into
    the worktree's branch (which stops on a conflict and leaves it to a builder, or is
    refused and leaves nothing), commit (which a hook may refuse), and the push of the commit
    named, never of whatever the branch holds then, with a lease on the commit Lem pushed last
    (`landing.md` H 3), None when the branch is new."""

    def fetch(self, where: Path) -> None: ...
    def rebase(
        self, worktree: Path, onto: str, *, reapply: bool
    ) -> Sha | Conflict | GitRefused: ...
    def abort(self, worktree: Path) -> None: ...
    def merge(
        self, worktree: Path, ref: str, message: str
    ) -> Sha | Conflict | GitRefused: ...
    def commit(
        self, worktree: Path, message: str, paths: tuple[str, ...]
    ) -> Sha | GitRefused: ...
    def push(
        self, worktree: Path, branch: str, expect: Sha | None, *, commit: Sha
    ) -> Sha | GitRefused: ...


class GitBranches(Protocol):
    """The acts on worktrees and branches: add and remove a worktree, add a branch with no
    worktree, move a worktree's branch back to a commit and delete a branch, each only at the
    commit named, and fast-forward a checkout."""

    def worktree_add(
        self, checkout: Path, path: Path, branch: str, start: str
    ) -> None: ...
    def worktree_remove(self, checkout: Path, path: Path) -> None: ...
    def branch_add(
        self, checkout: Path, branch: str, start: str
    ) -> Sha | GitRefused: ...
    def reset(self, worktree: Path, commit: Sha, expect: Sha) -> Sha | GitRefused: ...
    def branch_delete(self, checkout: Path, branch: str, expect: Sha) -> bool: ...
    def fast_forward(self, checkout: Path, ref: str) -> Sha | GitRefused: ...


class GitActs(GitRewrite, GitBranches, Protocol):
    """Every act."""


class Git(GitFacts, GitActs, Protocol):
    """The whole port."""
