"""The branch a task's worktree is on, read from the files git keeps: the worktree's `.git` names
its own git folder, whose `HEAD` is `ref: refs/heads/BRANCH` on a branch and a commit when
detached (`git branch --show-current`; `store.places` reads the same files).

The `Git` port has no such fact yet (`notes/land-base.md`); a step reads it here before it acts
on the branch, so that a detached HEAD at the branch's own commit is never taken for the
branch.
"""

from pathlib import Path

HEADS = "ref: refs/heads/"


def git_folder(worktree: Path) -> Path:
    """The worktree's own git folder: `.git` itself in a main checkout, else the folder its
    `.git` file names."""
    dot_git = worktree / ".git"
    if dot_git.is_dir():
        return dot_git
    named = dot_git.read_text(encoding="utf-8").strip().removeprefix("gitdir:").strip()
    folder = Path(named)
    return folder if folder.is_absolute() else (worktree / folder).resolve()


def branch_of(worktree: Path) -> str | None:
    """The branch the worktree's HEAD is on, or None when HEAD is detached or not there."""
    try:
        head = (git_folder(worktree) / "HEAD").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return head.removeprefix(HEADS) if head.startswith(HEADS) else None
