"""The backlog as the views read it (`board.backlog` on `main`): the items of the backlog folder
and the reviewer's items of the state folder, each with its head, its title and text, what git
says of it, and whether the place in the code it names is still there.

A file that does not read is an item that says so, never a backlog that stops.
"""

from lem.records.base import Frozen, Moment


class AddedBy(Frozen, frozen=True, kw_only=True):
    """The commit that added an item's file: its author and day, and the task or the pull
    request it names (`board.added_by` on `main`)."""

    author: str
    day: str
    task: str | None = None
    pull: str | None = None


class Entry(Frozen, frozen=True, kw_only=True):
    """One item: its path from the main checkout's root, its key on the page (the file's stem,
    `-STEM` for a reviewer's item), whether it is the reviewer's, its head's `worth`, `where`
    and `added`, its title and text, the commit that added it (None while git has no such
    commit), whether git tracks it and whether it changed since, why its `where` no longer
    resolves, and why it does not read."""

    path: str
    key: str
    reviewer: bool = False
    worth: str | None = None
    where: str | None = None
    added_on: str | None = None
    title: str = ""
    text: str = ""
    added: AddedBy | None = None
    tracked: bool = True
    changed: bool = False
    where_problem: str | None = None
    bad: str | None = None


class Shelved(Frozen, frozen=True, kw_only=True):
    """The read of the backlog: its folder, the reviewer's folder, the items in the order
    read, when, and why it did not read."""

    folder: str
    reviewer: str
    entries: tuple[Entry, ...] = ()
    read: Moment
    problem: str | None = None
