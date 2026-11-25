"""Where a task's files are: its folder in the state, its worktree under `.lem/worktrees/`,
and the branch it works on.

The worktrees' folder holds a `.gitignore` of `*`, so the main checkout's `git status` never
shows a task's worktree (`project.cmd_worktree_dir` on `main`).
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record
    from lem.settings.team import Branch

WORKTREES = "worktrees"


def worktrees(workspace: places.Workspace) -> Path:
    """The folder of the tasks' worktrees, made with its ignore file when it is not there."""
    folder = workspace.lem / WORKTREES
    folder.mkdir(parents=True, exist_ok=True)
    ignore = folder / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("*\n", encoding="utf-8")
    return folder


def worktree(workspace: places.Workspace, slug: str) -> Path:
    """The path of the worktree of the task `slug`."""
    places.task_folder(workspace.state, slug)
    return worktrees(workspace) / slug


def branch(record: Record) -> str:
    """The branch the task works on; refused before its worktree named one."""
    named = record.task.branch
    if named is None:
        slug = record.task.slug
        raise Refusal(
            "no-branch",
            f"{slug} has no branch yet",
            f"lem task worktree {slug} makes its worktree on its branch",
        )
    return named


def named(record: Record, asked: str | None, rules: Branch) -> str:
    """The task's branch: the one asked for, else on record, else TYPE/SLUG; never the base
    or a protected one (`rules`)."""
    shape, slug = record.task.shape, record.task.slug
    chosen = asked or record.task.branch
    if chosen is None and shape is not None:
        chosen = f"{shape.type}/{slug}"
    if chosen is None:
        raise Refusal(
            "no-branch",
            "the task has no type yet, so no branch TYPE/SLUG",
            "lem task read SLUG gives its type first, or --branch names the branch",
        )
    if chosen == rules.base or chosen in rules.protected:
        raise Refusal(
            "protected",
            f"{chosen} is the base or a protected branch: a task works on a branch of its own",
            "name another with --branch",
        )
    return chosen
