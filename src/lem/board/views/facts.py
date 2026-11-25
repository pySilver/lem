"""The facts beside a task's record that a view reads: the newest commit of its branch, a backlog
item the branch adds, and a file of its folder."""

from lem.records.base import Frozen, Moment, Sha


class Commit(Frozen, frozen=True, kw_only=True):
    """The newest commit of a task's branch: its id and its subject."""

    sha: Sha
    subject: str


class Filed(Frozen, frozen=True, kw_only=True):
    """A backlog item the task's branch adds: its path and its title."""

    path: str
    title: str


class Stat(Frozen, frozen=True, kw_only=True):
    """A file of a task's folder: its path, its bytes, and when it changed."""

    path: str
    size: int
    changed: Moment
