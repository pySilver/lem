"""The list `lem uninstall` shows before its one question: what goes, what stays, and what is
left for the owner."""

from typing import TYPE_CHECKING

from lem.adapters.claude_plugin import PLUGIN
from lem.cli.uninstall.claude import MARKET

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.cli.uninstall.found import Found
    from lem.cli.uninstall.repos import Repo


def lines(found: Found) -> Iterator[str]:
    """The list, one line for each thing."""
    yield "Lem stops the board server of this computer, and closes its tailnet door if open."
    for scope in found.plugins:
        yield f"Lem removes the plugin {PLUGIN} from the {scope.name} scope of {scope.folder}."
    for scope in found.markets:
        yield f"Lem removes the marketplace {MARKET} from the {scope.name} scope of {scope.folder}."
    both = " and ".join(found.rules)
    for path in found.holders:
        yield f"Lem removes {both} from {path}."
    for repo in found.repos:
        yield from repository(repo)
    for job in found.jobs or ():
        yield f"The owner deletes the cronn job {job.command!r} from {found.jobs_file}."
    yield f"Lem removes {found.home} and {found.pages}."
    yield "The other files of each .lem/ stay: they are the team's files in git."


def repository(repo: Repo) -> Iterator[str]:
    """The lines of one repository."""
    for slug in repo.open:
        yield f"The open task {slug} keeps its worktree, its branch and {repo.state}."
    if repo.state.exists() or repo.worktrees.exists():
        yield (
            f"With 'all', Lem removes {repo.state} and the worktrees of {repo.worktrees} "
            "of the tasks that ended, by git worktree remove."
        )
    for branch in repo.branches:
        yield f"The branch {branch} of {repo.root} stays."
