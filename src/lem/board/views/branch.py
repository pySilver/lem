"""What git says of a task's branch, for its board (`board.filed` and the last commit on
`main`): the newest commit, and the backlog items the branch adds against its merge base.

Each fact is None when git is not asked or cannot tell (no branch, no merge base): the page then
says nothing, never that none was filed.
"""

from typing import TYPE_CHECKING, Protocol

from lem.board.views.backlog import head
from lem.board.views.facts import Commit, Filed

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import Place
    from lem.ports.git_facts import Commit as Logged
    from lem.records.task import Task


class Branches(Protocol):
    """The facts of the `Git` port that a task's board reads."""

    def tip(self, where: Path, ref: str) -> str | None: ...
    def merge_base(self, where: Path, first: str, second: str) -> str | None: ...
    def commits(self, where: Path, since: str, until: str) -> tuple[Logged, ...]: ...
    def changed_paths(self, where: Path, since: str, until: str) -> tuple[str, ...]: ...
    def show(self, where: Path, rev: str, path: str) -> bytes | None: ...


def head_of(
    git: Branches | None, checkout: Path, task: Task, place: Place
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
    git: Branches | None, checkout: Path, task: Task, place: Place
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
        filed_item(git.show(checkout, tip, path), path) for path in sorted(added)
    )


def in_folder(path: str, folder: str) -> bool:
    """Whether `path` is an item of the backlog folder itself, not of a folder under it."""
    return path.endswith(".md") and path.rpartition("/")[0] == folder


def filed_item(body: bytes | None, path: str) -> Filed:
    """The item, with its heading even when the front matter does not read."""
    raw = (body or b"").decode(errors="replace")
    parsed = head.parse(raw)
    stem = path.rpartition("/")[2].removesuffix(".md")
    if isinstance(parsed, head.Head):
        return Filed(path=path, title=parsed.title or stem)
    heading = head.TITLE.search(raw)
    title = heading[1].replace("`", "").strip() if heading else stem
    return Filed(path=path, title=title or stem, problem=parsed)
