"""The acts of the `Git` port through real git: a task branch's rewrite (`GitRewrite`) and the
worktrees and branches (`GitBranches`).

A push carries a lease on the commit Lem pushed last, or on no branch at all when it is new
(`landing.md` H 3); a branch is deleted only at the commit named, and never while a worktree
has it.
"""

from typing import TYPE_CHECKING

from lem.adapters.git_cli_shell import GIT, QUIET, Shell, all_words, last_words
from lem.adapters.git_cli_stops import conflicted, rebase_folder
from lem.ports.faults import Unanswered
from lem.ports.git_facts import Conflict, GitRefused

if TYPE_CHECKING:
    from pathlib import Path

HEADS = "refs/heads/"
WORKTREE = "worktree"


class Rewrite(Shell):
    """Fetch, rebase and its abort, commit, and a push with a lease."""

    def fetch(self, where: Path) -> None:
        self.said(where, "fetch", QUIET, "--prune", "origin")

    def rebase(
        self, worktree: Path, onto: str, *, reapply: bool
    ) -> str | Conflict | GitRefused:
        chosen = ("--reapply-cherry-picks",) if reapply else ()
        ran = self.tried(worktree, "rebase", QUIET, *chosen, onto)
        if not ran.returncode:
            return self.head(worktree)
        stopped = conflicted(self, worktree) if rebase_folder(self, worktree) else ()
        if stopped:
            return Conflict(files=stopped)
        return GitRefused(said=all_words(ran))

    def abort(self, worktree: Path) -> None:
        self.said(worktree, "rebase", "--abort")

    def commit(self, worktree: Path, message: str, paths: tuple[str, ...]) -> str:
        self.said(worktree, "add", "--all", "--", *paths)
        self.said(worktree, "commit", QUIET, "--message", message, "--", *paths)
        return self.head(worktree)

    def push(self, worktree: Path, branch: str, expect: str | None) -> str | GitRefused:
        ref = HEADS + branch
        there = self.on_origin(worktree, ref)
        if there != (expect or ""):
            # git checks no lease for a push that changes nothing, so it is read here too
            return GitRefused(said=f"stale info: origin's {ref} is not {expect}")
        lease = f"--force-with-lease={ref}:{there}"
        both = f"{ref}:{ref}"
        ran = self.tried(worktree, "push", QUIET, lease, "origin", both)
        if ran.returncode:
            return GitRefused(said=last_words(ran))
        return self.said(worktree, "rev-parse", ref)

    def on_origin(self, where: Path, ref: str) -> str:
        """The commit origin has at `ref` now, or an empty text when it has none."""
        listed = self.said(where, "ls-remote", "origin", ref)
        return listed.split("\t", 1)[0]


class Branches(Shell):
    """Add and remove a worktree, delete a branch at the commit named, and fast-forward a
    checkout that is on the branch of the ref (`origin/main` moves `main` only)."""

    def worktree_add(self, checkout: Path, path: Path, branch: str, start: str) -> None:
        if path.exists():
            raise Unanswered(GIT, f"'{path}' already exists")
        if self.commit_at(checkout, HEADS + branch):
            self.said(checkout, WORKTREE, "add", QUIET, str(path), branch)
            return
        made = ("--no-track", "-b", branch, str(path), start)
        self.said(checkout, WORKTREE, "add", QUIET, *made)

    def worktree_remove(self, checkout: Path, path: Path) -> None:
        self.said(checkout, WORKTREE, "remove", str(path))

    def branch_delete(self, checkout: Path, branch: str, expect: str) -> bool:
        if self.checked_out(checkout, branch):
            return False
        ran = self.tried(checkout, "update-ref", "-d", HEADS + branch, expect)
        return not ran.returncode

    def fast_forward(self, checkout: Path, ref: str) -> str | GitRefused:
        named = ref.removeprefix("origin/")
        current = self.tried(checkout, "symbolic-ref", QUIET, "--short", "HEAD")
        if current.stdout.strip() != named:
            on = current.stdout.strip() or "a detached HEAD"
            return GitRefused(said=f"the checkout is on {on}, not on {named}")
        ran = self.tried(checkout, "merge", "--ff-only", QUIET, ref)
        if ran.returncode:
            return GitRefused(said=last_words(ran))
        return self.head(checkout)

    def checked_out(self, checkout: Path, branch: str) -> bool:
        """Whether a worktree of the repository has `branch` checked out."""
        listed = self.said(checkout, WORKTREE, "list", "--porcelain")
        return f"branch {HEADS}{branch}" in listed.splitlines()
