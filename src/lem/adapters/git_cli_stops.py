"""A rebase or a merge that stopped, as the `git` adapter reads it: whether one is in progress in
a worktree, and the files it waits on."""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.adapters.git_cli_names import listed
from lem.adapters.git_cli_shell import GIT
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from lem.adapters.git_cli_shell import Shell

# The folders of a worktree's own git folder that hold a rebase in progress.
REBASE_FOLDERS = ("rebase-merge", "rebase-apply")
ABSOLUTE = "--path-format=absolute"
UNMERGED = "--diff-filter=U"


def rebase_folder(shell: Shell, where: Path) -> Path | None:
    """The folder of the rebase in progress in the worktree `where`, or None."""
    for name in REBASE_FOLDERS:
        found = Path(shell.said(where, "rev-parse", ABSOLUTE, "--git-path", name))
        if found.is_dir():
            return found
    return None


def conflicted(shell: Shell, where: Path) -> tuple[str, ...]:
    """The files a stopped rebase left in conflict in `where`, shown (`git_cli_names`); with
    none unmerged, the files the stopped commit staged: git's recorded resolution of a
    conflict, which it stages by itself with `rerere.autoupdate`, still waits for a
    builder."""
    for which in (UNMERGED, "--cached"):
        found = named_by(shell, where, which)
        if found:
            return found
    return ()


def named_by(shell: Shell, where: Path, which: str) -> tuple[str, ...]:
    """The files `git diff WHICH` names in `where`, shown and sorted."""
    ran = shell.raw(where, "diff", which, "-z", "--name-only")
    if ran.returncode:
        said = ran.stderr.decode(errors="replace").strip()
        raise Unanswered(GIT, said or f"git diff exited {ran.returncode}")
    return tuple(sorted(listed(ran.stdout)))


def merge_stopped(shell: Shell, where: Path) -> tuple[str, ...] | None:
    """The files a merge that stopped in `where` left unmerged; an empty tuple for a merge
    that stopped with none (a hook that refused its commit), None for no merge in progress."""
    if shell.commit_at(where, "MERGE_HEAD") is None:
        return None
    return named_by(shell, where, UNMERGED)


def too_old(shell: Shell, where: Path, said: bytes) -> str:
    """Why `git merge-tree --write-tree` gave no tree: git's words, and its version, since a
    git older than 2.38 has no `--write-tree`."""
    words = said.decode(errors="replace").strip() or "no tree"
    version = shell.tried(where, "--version").stdout.strip()
    return (
        f"git merge-tree failed ({words}); `git merge-tree --write-tree` needs git 2.38 "
        f"or newer, and `git --version` says {version}: the owner updates git, and the "
        "step runs again"
    )
