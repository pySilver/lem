"""What git says of the backlog folder's items (`board.added_by` and the status read of
`board.backlog` on `main`): the commit that added each file, with the task or the pull request it
names, and the files git has no commit of, or a change since.

Git comes in through `Ledger`, the facts of the `Git` port this read needs; the rules over its
answers are pure, so a test gives them as values.
"""

import re
from typing import TYPE_CHECKING, Protocol

from lem.board.views.backlog_read import AddedBy
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

# A path git has no commit of or a change to, with its two letters of `git status --porcelain`.
type Unsaved = tuple[tuple[str, str], ...]

# The task a commit that added an item names, from git alone, so that every clone shows the
# same line: the line Lem's squash merge ends its body with, then the subject of the commit
# that files a review's items on the branch; else the pull request its subject ends with, as
# GitHub's squash writes it.
TASK_LINE = re.compile(r"(?m)^Lem task:[ \t]*([a-z0-9]+(?:-[a-z0-9]+)*)[ \t]*$")
FILE_SUBJECT = re.compile(
    r"^docs\(backlog\): what review round \d+ saw outside "
    r"([a-z0-9]+(?:-[a-z0-9]+)*)(?: \(#\d+\))?$"
)
PULL_SUBJECT = re.compile(r"\(#(\d+)\)\s*$")


class Adding(Frozen, frozen=True, kw_only=True):
    """A commit that added files under the backlog folder: its author, its day, its subject
    and body, and the paths it added."""

    author: str
    day: str
    subject: str
    body: str = ""
    paths: tuple[str, ...] = ()


class Ledger(Protocol):
    """The facts of git the backlog's read takes, each None when git cannot tell."""

    def adds(self, where: Path, folder: str) -> tuple[Adding, ...] | None:
        """Each commit that added a file under `folder`, the newest first (`git log
        --diff-filter=A --no-renames --date=short --name-only -- FOLDER`)."""
        ...

    def unsaved(self, where: Path, folder: str) -> Unsaved | None:
        """Each path under `folder` git has no commit of or a change to, file by file in a
        folder git does not know yet, with its two letters (`git status --porcelain
        --untracked-files=all -- FOLDER`)."""
        ...


def added_by(adds: tuple[Adding, ...], folder: str) -> dict[str, AddedBy]:
    """By the path of each item of `folder`, the newest commit that added its file; a file in
    a folder under it is no item."""
    found: dict[str, AddedBy] = {}
    for commit in adds:
        for path in commit.paths:
            if is_item(path, folder) and path not in found:
                found[path] = whose(commit)
    return found


def whose(commit: Adding) -> AddedBy:
    """The author and day of a commit, and the task or the pull request it names."""
    subject = commit.subject.strip()
    named = TASK_LINE.search(commit.body) or FILE_SUBJECT.match(subject)
    pull = None if named else PULL_SUBJECT.search(commit.subject)
    return AddedBy(
        author=commit.author.strip(),
        day=commit.day.strip(),
        task=named[1] if named else None,
        pull=pull[1] if pull else None,
    )


def is_item(path: str, folder: str) -> bool:
    """Whether `path` is an item of the folder itself."""
    return path.endswith(".md") and path.rpartition("/")[0] == folder


def changes(unsaved: Unsaved) -> tuple[frozenset[str], frozenset[str]]:
    """The paths git has no commit of (untracked, or added to the index only), and the
    paths it has with a change since."""
    new = frozenset(path for code, path in unsaved if is_added(code))
    edited = frozenset(path for _, path in unsaved) - new
    return new, edited


def is_added(code: str) -> bool:
    """Whether the two letters of a path say git has no commit of it: untracked, or added to
    the index only."""
    return code == "??" or "A" in code
