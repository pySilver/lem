"""A real git repository in a temporary folder, for the steps that need real git: a bare
`origin`, the main checkout cloned from it, and a teammate's clone for what someone else pushes.

Git runs with the test's own HOME (the entry's), no system configuration, and a fixed author, so
that no setting of the machine (a hook, a signature, a default branch) reaches a test. `merge_into`
and `delete_remote` act on `origin` the way the forge does, for `LocalForge` over real git.
"""

import os
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from fakes.git import Landed
from lem.ports.git_facts import Conflict

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.forge_facts import MergeMethod

AUTHOR = {
    "GIT_AUTHOR_NAME": "Lem Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Lem Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git_env() -> dict[str, str]:
    """The environment every git of a test runs with."""
    return {
        **os.environ,
        **AUTHOR,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }


def run_git(where: Path, *args: str) -> str:
    """`git -C WHERE ARGS`, its output without the last line end; a test fails when git does."""
    ran = subprocess.run(
        ["git", "-C", str(where), *args],
        capture_output=True,
        text=True,
        env=git_env(),
        check=False,
        timeout=60,
    )
    if ran.returncode:
        raise AssertionError(f"git {' '.join(args)} in {where}: {ran.stderr}")
    return ran.stdout.rstrip("\n")


def write(where: Path, files: dict[str, bytes | None]) -> None:
    """Write `files` into a worktree; None removes the file."""
    for path, body in files.items():
        target = where / path
        if body is None:
            target.unlink(missing_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)


@dataclass(frozen=True)
class RealRepo:
    """The origin, the main checkout, and a teammate's clone."""

    origin: Path
    checkout: Path
    teammate: Path
    branch: str

    @classmethod
    def init(
        cls, folder: Path, files: dict[str, bytes], branch: str = "main"
    ) -> RealRepo:
        """A repository in `folder` with one commit of `files` on `branch`, pushed."""
        origin, checkout, teammate = (
            folder / "origin.git",
            folder / "checkout",
            folder / "teammate",
        )
        folder.mkdir(parents=True, exist_ok=True)
        run_git(
            folder,
            "init",
            "--quiet",
            "--bare",
            f"--initial-branch={branch}",
            str(origin),
        )
        run_git(folder, "clone", "--quiet", str(origin), str(checkout))
        write(checkout, dict(files))
        run_git(checkout, "add", "--all")
        run_git(checkout, "commit", "--quiet", "--message", "the first commit")
        run_git(checkout, "push", "--quiet", "origin", branch)
        run_git(folder, "clone", "--quiet", str(origin), str(teammate))
        return cls(origin=origin, checkout=checkout, teammate=teammate, branch=branch)

    def outside_commit(
        self, branch: str, files: dict[str, bytes | None], start: str = "main"
    ) -> str:
        """A commit the teammate pushes to `branch` on the origin, made from the origin's
        `start` when the branch is new."""
        run_git(self.teammate, "fetch", "--quiet", "origin")
        source = branch if self.head_of(branch) else start
        run_git(self.teammate, "checkout", "--quiet", "-B", branch, f"origin/{source}")
        write(self.teammate, files)
        run_git(self.teammate, "add", "--all")
        run_git(
            self.teammate,
            "commit",
            "--quiet",
            "--message",
            f"outside: {', '.join(files)}",
        )
        run_git(self.teammate, "push", "--quiet", "origin", branch)
        return run_git(self.teammate, "rev-parse", "HEAD")

    def outside_merge_commit(
        self, branch: str, other: str, files: dict[str, bytes]
    ) -> str:
        """A merge commit of the origin's `other` into its `branch` that the teammate pushes,
        with `files` edited in the merge itself."""
        run_git(self.teammate, "fetch", "--quiet", "origin")
        run_git(self.teammate, "checkout", "--quiet", "-B", branch, f"origin/{branch}")
        run_git(
            self.teammate,
            "merge",
            "--quiet",
            "--no-ff",
            "--no-commit",
            f"origin/{other}",
        )
        write(self.teammate, dict(files))
        run_git(self.teammate, "add", "--all")
        run_git(self.teammate, "commit", "--quiet", "--message", f"Merge {other}")
        run_git(self.teammate, "push", "--quiet", "origin", branch)
        return run_git(self.teammate, "rev-parse", "HEAD")

    def head_of(self, branch: str) -> str | None:
        """The origin's `branch`, or None."""
        listed = run_git(
            self.origin,
            "for-each-ref",
            "--format=%(objectname)",
            f"refs/heads/{branch}",
        )
        return listed or None

    def tree_of_merge(
        self, ours: str, theirs: str, base: str | None = None
    ) -> str | Conflict:
        """The tree `git merge-tree` makes of two commits in the origin, or the conflict."""
        chosen = [f"--merge-base={base}"] if base else []
        ran = subprocess.run(
            [
                "git",
                "-C",
                str(self.origin),
                "merge-tree",
                "--write-tree",
                "--name-only",
                *chosen,
                ours,
                theirs,
            ],
            capture_output=True,
            text=True,
            env=git_env(),
            check=False,
            timeout=60,
        )
        lines = ran.stdout.splitlines()
        if ran.returncode == 1:
            files = tuple(
                line
                for line in lines[1:]
                if line and not line.startswith(("Auto-merging", "CONFLICT"))
            )
            return Conflict(files=files)
        if ran.returncode:
            raise AssertionError(f"git merge-tree in {self.origin}: {ran.stderr}")
        return lines[0]

    def merge_into(
        self, base: str, head: str, *, method: MergeMethod, message: str
    ) -> Landed | Conflict:
        """Merge the commit `head` into the origin's `base`, as the forge does: one squashed
        commit, a merge commit, or each commit but a merge replayed."""
        target = run_git(self.origin, "rev-parse", f"refs/heads/{base}")
        if method == "rebase":
            made = self.replayed(target, head)
            if isinstance(made, Conflict):
                return made
        else:
            tree = self.tree_of_merge(target, head)
            if isinstance(tree, Conflict):
                return tree
            parents = (
                ["-p", target] if method == "squash" else ["-p", target, "-p", head]
            )
            made = run_git(self.origin, "commit-tree", tree, *parents, "-m", message)
        run_git(self.origin, "update-ref", f"refs/heads/{base}", made, target)
        return Landed(commit=made, base_parent=target)

    def replayed(self, onto: str, head: str) -> str | Conflict:
        """Each commit of `head` that `onto` lacks, but a merge, replayed onto `onto`."""
        listed = run_git(
            self.origin, "rev-list", "--reverse", "--no-merges", f"{onto}..{head}"
        )
        current = onto
        for sha in listed.split():
            tree = self.tree_of_merge(current, sha, base=f"{sha}^")
            if isinstance(tree, Conflict):
                return tree
            message = run_git(self.origin, "log", "-1", "--format=%B", sha)
            current = run_git(
                self.origin, "commit-tree", tree, "-p", current, "-m", message
            )
        return current

    def delete_remote(self, branch: str, expect: str) -> bool:
        """Delete the origin's `branch` only at `expect`."""
        ran = subprocess.run(
            [
                "git",
                "-C",
                str(self.origin),
                "update-ref",
                "-d",
                f"refs/heads/{branch}",
                expect,
            ],
            capture_output=True,
            env=git_env(),
            check=False,
            timeout=60,
        )
        return ran.returncode == 0
