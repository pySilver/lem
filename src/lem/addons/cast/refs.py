"""The default branch and whether a worktree changed a path of its own."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.adapters.git_cli_shell import Shell
from lem.kernel.errors import Refusal
from lem.store.places import checkout_of

if TYPE_CHECKING:
    from pathlib import Path


REV = "rev-parse"


@dataclass(frozen=True, slots=True)
class Checkout:
    """The active worktree, and git with the current environment."""

    path: Path
    git: Shell

    def text(self, *args: str) -> str:
        """The stripped answer when git answers, otherwise no ref or path."""
        ran = self.git.tried(self.path, *args)
        return ran.stdout.strip() if ran.returncode == 0 else ""

    def succeeds(self, *args: str) -> bool:
        """Whether git confirms a comparison."""
        return self.git.tried(self.path, *args).returncode == 0

    def has_commit(self, ref: str) -> bool:
        """Whether the reference names a commit."""
        return self.git.commit_at(self.path, ref) is not None

    def blob(self, ref: str, path: str) -> bytes:
        """Read a known blob by its ref and path."""
        return self.git.blob(self.path, f"{ref}:{path}")


def checkout(folder: Path) -> Checkout:
    """Resolve the active worktree and check the repository boundary."""
    checkout_of(folder)
    git = Shell(environ=os.environ)
    ran = Checkout(folder, git).text(REV, "--show-toplevel")
    if not ran:
        raise Refusal(
            "cast-checkout", "Git found no worktree", "use lem --repo WORKTREE cast"
        )
    return Checkout(folder / ran, git)


def refs(git: Checkout) -> tuple[str, ...]:
    """Read the configured origin branch, with the newer available ref first."""
    origin = git.text("symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    branches = (
        (origin.removeprefix("refs/remotes/origin/"),)
        if origin
        else ("main", "master", "trunk")
    )
    return tuple(ref for branch in branches for ref in ordered(git, branch))


def ordered(git: Checkout, branch: str) -> tuple[str, ...]:
    """Prefer the ref that contains the other. Prefer local when they diverge."""
    local, remote = f"refs/heads/{branch}", f"refs/remotes/origin/{branch}"
    offered = (local, remote)
    present = tuple(filter(git.has_commit, offered))
    if present == (local, remote) and git.succeeds(
        "merge-base", "--is-ancestor", local, remote
    ):
        return tuple(reversed(present))
    return present


def follows(git: Checkout, ref: str, path: str) -> bool:
    """A worktree with a committed or pending edit keeps its own copy."""
    base = git.text("merge-base", "HEAD", ref)
    return bool(
        base
        and git.succeeds("diff", "--quiet", base, "HEAD", "--", path)
        and not git.text("status", "--porcelain", "--untracked-files=all", "--", path)
        and git.text(REV, "--verify", f"HEAD:{path}")
        != git.text(REV, "--verify", f"{ref}:{path}")
    )
