"""The repositories of the board's list as `lem uninstall` reads and cleans them: the open
tasks, the task worktrees under `.lem/worktrees/` and the task branches that still exist.

A worktree goes by `git worktree remove`, never by a removal of its folder, and then `git
worktree prune`, so git keeps no record of it; git refuses one with changes no commit holds.
The worktree of an open task, the state of its repository and every task branch stay.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.app.tasks.where import WORKTREES
from lem.board import workspaces
from lem.cli.uninstall import computer
from lem.kernel import folders
from lem.kernel.errors import Refusal
from lem.store import places, tasks
from lem.store.retention.rules import ENDED

if TYPE_CHECKING:
    from lem.adapters.git_cli import GitCli
    from lem.cli.uninstall.report import Report


class Repo(msgspec.Struct, frozen=True, kw_only=True):
    """One repository: its main checkout, the slugs of its open tasks, the folders under
    `.lem/worktrees/`, and the task branches that still exist."""

    root: Path
    open: tuple[str, ...]
    trees: tuple[Path, ...]
    branches: tuple[str, ...]

    @property
    def state(self) -> Path:
        """The repository's `.lem/state/`."""
        return self.root / places.STATE

    @property
    def worktrees(self) -> Path:
        """The repository's `.lem/worktrees/`."""
        return self.root / ".lem" / WORKTREES


def listed(home: Path, git: GitCli) -> tuple[Repo, ...]:
    """Each repository of the board's list; refused when one is not there, since its open
    tasks cannot be read."""
    names = workspaces.listed(home)
    return tuple(read(Path(name), git) for name in names)


def read(root: Path, git: GitCli) -> Repo:
    """One repository as it is now."""
    folders.inside_test_root(root)
    if not root.is_dir():
        raise Refusal(
            "uninstall-workspace",
            f"the repository {root} of the board's list is not there, so Lem cannot read "
            "its open tasks",
            f"the owner makes {root} available again, or takes it off the list with "
            f"lem serve remove {root}",
        )
    records = [record.task for record in tasks.every(root / places.STATE)]
    named = sorted({task.branch for task in records if task.branch})
    folder = root / ".lem" / WORKTREES
    trees = (
        sorted(one for one in folder.iterdir() if one.is_dir())
        if folder.is_dir()
        else []
    )
    return Repo(
        root=root,
        open=tuple(task.slug for task in records if task.status not in ENDED),
        trees=tuple(trees),
        branches=tuple(
            one for one in named if git.commit_at(root, f"refs/heads/{one}")
        ),
    )


def guarded(repos: tuple[Repo, ...], *, force: bool) -> None:
    """Refused, before any removal, while a repository has an open task and the owner did not
    say `--force`."""
    opened = [f"{slug} in {repo.root}" for repo in repos for slug in repo.open]
    if opened and not force:
        named = ", ".join(opened)
        raise Refusal(
            "uninstall-open-tasks",
            f"these tasks are open: {named}",
            "the owner lands or drops each of them, or runs lem uninstall --force, which "
            "keeps their worktrees, their branches and the state of their repositories",
        )


def cleaned(git: GitCli, repo: Repo, report: Report, *, remove: bool) -> None:
    """The repository's task branches stay; its state and worktrees go when `remove`."""
    for branch in repo.branches:
        report.stays(f"the branch {branch} of {repo.root}")
    failed = len(report.failed)
    if remove:
        removed_trees(git, repo, report)
    if not remove or repo.open or len(report.failed) > failed:
        for place in (repo.state, repo.worktrees):
            if place.exists():
                report.stays(str(place))
        return
    with report.step(str(repo.worktrees), f"the owner looks into {repo.worktrees}"):
        computer.emptied(repo.worktrees)
    computer.removed(repo.state, report)


def removed_trees(git: GitCli, repo: Repo, report: Report) -> None:
    """Each worktree of an ended task through git, then git's prune."""
    for tree in repo.trees:
        if tree.name in repo.open:
            report.stays(f"the worktree {tree} of the open task {tree.name}")
            continue
        with report.step(
            f"git worktree remove {tree}",
            f"the owner reads git's words, then runs git worktree remove {tree}",
        ):
            git.worktree_remove(repo.root, tree)
            report.gone(f"the worktree {tree}")
    with report.step(
        f"git worktree prune in {repo.root}", "the owner reads git's words"
    ):
        git.said(repo.root, "worktree", "prune")
