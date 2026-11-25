"""What git says of a task's branch, for its board (`board.filed` and the last commit on
`main`): the newest commit, and the backlog items the branch adds against its merge base.

Each fact is None when git is not asked or cannot tell (no branch, no merge base): the page then
says nothing, never that none was filed.
"""

from typing import TYPE_CHECKING

import frontmatter

from lem.board.views.world import Commit, Filed

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import Place
    from lem.ports.git import GitFacts
    from lem.records.task import Task


def head_of(
    git: GitFacts | None, checkout: Path, task: Task, place: Place
) -> Commit | None:
    """The newest commit of the task's branch, or None."""
    tip = git.tip(checkout, task.branch) if git and task.branch else None
    if git is None or tip is None:
        return None
    since = git.merge_base(checkout, place.base, tip) or f"{tip}^"
    commits = git.commits(checkout, since, tip)
    newest = next((one for one in commits if one.sha == tip), None)
    return Commit(sha=tip, subject=newest.subject if newest else "")


def filed_of(
    git: GitFacts | None, checkout: Path, task: Task, place: Place
) -> tuple[Filed, ...] | None:
    """The backlog items the task's branch adds, or None when git cannot tell."""
    tip = git.tip(checkout, task.branch) if git and task.branch else None
    since = git.merge_base(checkout, place.base, tip) if git and tip else None
    if git is None or tip is None or since is None:
        return None
    paths = git.changed_paths(checkout, since, tip)
    added = [
        path
        for path in paths
        if in_folder(path, place.backlog) and git.show(checkout, since, path) is None
    ]
    return tuple(
        Filed(path=path, title=title_of(git.show(checkout, tip, path), path))
        for path in sorted(added)
    )


def in_folder(path: str, folder: str) -> bool:
    """Whether `path` is an item of the backlog folder itself, not of a folder under it."""
    return path.endswith(".md") and path.rpartition("/")[0] == folder


def title_of(body: bytes | None, path: str) -> str:
    """The `# TITLE` of an item's text, else its file's stem."""
    text = frontmatter.loads((body or b"").decode(errors="replace")).content
    heading = next(
        (line[2:].strip() for line in text.splitlines() if line.startswith("# ")), ""
    )
    return heading.replace("`", "") or path.rpartition("/")[2].removesuffix(".md")
