"""The acts of the `Git` port through real git: a task branch's rewrite (`GitRewrite`) and the
worktrees and branches (`GitBranches`).

A push sends the commit named, never what the branch holds by then, with a lease on the commit
Lem pushed last, or on no branch at all when it is new (`landing.md` H 3); a branch moves back
or is deleted only at the commit named, and is never deleted while a worktree has it.
"""

from typing import TYPE_CHECKING

from lem.adapters.git_cli_facts import clean
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
        return GitRefused(said=all_words(ran.stderr))

    def abort(self, worktree: Path) -> None:
        self.said(worktree, "rebase", "--abort")

    def commit(
        self, worktree: Path, message: str, paths: tuple[str, ...]
    ) -> str | GitRefused:
        self.said(worktree, "add", "--all", "--", *paths)
        made = ("commit", QUIET, "--message", message, "--", *paths)
        ran = self.tried(worktree, *made)
        if ran.returncode:
            return GitRefused(said=all_words(ran.stderr or ran.stdout))
        return self.head(worktree)

    def push(
        self, worktree: Path, branch: str, expect: str | None, *, commit: str
    ) -> str | GitRefused:
        ref = HEADS + branch
        there = self.on_origin(worktree, ref)
        if there != (expect or ""):
            # git checks no lease for a push that changes nothing, so it is read here too
            return GitRefused(said=f"stale info: origin's {ref} is not {expect}")
        lease = f"--force-with-lease={ref}:{there}"
        sent = f"{commit}:{ref}"
        ran = self.tried(worktree, "push", QUIET, lease, "origin", sent)
        if ran.returncode:
            return GitRefused(said=last_words(ran))
        return commit

    def on_origin(self, where: Path, ref: str) -> str:
        """The commit origin has at `ref` now, or an empty text when it has none."""
        listed = self.said(where, "ls-remote", "origin", ref)
        return listed.split("\t", 1)[0]


class Branches(Shell):
    """Add and remove a worktree, add a branch, move a branch back and delete one at the
    commit named, and fast-forward a checkout that is on the branch of the ref (`origin/main`
    moves `main` only)."""

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

    def branch_add(self, checkout: Path, branch: str, start: str) -> str | GitRefused:
        ran = self.tried(checkout, "branch", "--no-track", branch, start)
        if ran.returncode:
            return GitRefused(said=last_words(ran))
        return self.said(checkout, "rev-parse", HEADS + branch)

    def reset(self, worktree: Path, commit: str, expect: str) -> str | GitRefused:
        if self.head(worktree) != expect:
            return GitRefused(said=f"the branch is not at {expect}")
        if not clean(self, worktree):
            return GitRefused(said="the worktree has changes that no commit holds")
        ran = self.tried(worktree, "reset", QUIET, "--keep", commit)
        if ran.returncode:
            return GitRefused(said=last_words(ran))
        return self.head(worktree)

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
