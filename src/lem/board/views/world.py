"""What the views of a workspace read: each task's record and what lies beside it, the owner's
presence, the tasks' sessions as the terminal showed them, the backlog, the Inbox's record, the
look at the forge, and who asks for the page at what minute.

A view is a pure function of this value: `gather.py` reads it from a workspace once for a page,
and a test builds it from the records it holds.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.records.base import Frozen, Sha
from lem.records.owner import Presence

if TYPE_CHECKING:
    from datetime import datetime, tzinfo

    from lem.app.sessions.acts import Act
    from lem.board.inputs.layout import Viewer
    from lem.board.views.backlog_read import Shelved
    from lem.board.views.inbox_read import Inbox
    from lem.model.owner.looks import Session, Stop
    from lem.records.record import Record


class Commit(Frozen, frozen=True, kw_only=True):
    """The newest commit of a task's branch: its id and its subject."""

    sha: Sha
    subject: str


class Filed(Frozen, frozen=True, kw_only=True):
    """A backlog item the task's branch adds: its path and its title."""

    path: str
    title: str


class Seen(Frozen, frozen=True, kw_only=True):
    """A task's record and what lies beside it: Lem's acts on its sessions, the files of its
    folder, the prose it shows read as it is (`task.md`, a breaker's document, the merge
    review), the newest commit of its branch, the backlog items its branch adds (None when git
    cannot tell), whether its worktree is there, its live session as the terminal shows it, and
    the guard's stop that stands over it."""

    record: Record
    acts: tuple[Act, ...] = ()
    files: tuple[str, ...] = ()
    prose: tuple[tuple[str, str], ...] = ()
    head: Commit | None = None
    filed: tuple[Filed, ...] | None = None
    worktree: bool = False
    session: Session | None = None
    stop: Stop | None = None

    def text(self, name: str) -> str | None:
        """The prose of the file `name` of the task's folder, or None when it is not there."""
        return next((body for path, body in self.prose if path == name), None)


@dataclass(frozen=True, kw_only=True, slots=True)
class Clock:
    """The minute of the page and the zone its clock reads in."""

    now: datetime
    zone: tzinfo


@dataclass(frozen=True, kw_only=True, slots=True)
class Place:
    """The workspace: its repository's name, the base branch its tasks land on, the path of
    its main checkout, and its backlog folder."""

    repo: str
    base: str
    path: str
    backlog: str = "docs/backlog"


@dataclass(frozen=True, kw_only=True, slots=True)
class Forge:
    """The board server's last look at the forge: when, why it failed, and the tasks whose
    pull request it called conflicting at the head Lem proposed last."""

    looked: datetime | None = None
    problem: str | None = None
    conflicts: frozenset[str] = frozenset()


@dataclass(frozen=True, kw_only=True, slots=True)
class World:
    """One workspace at the minute of a page: who asks, the clock, the version of the state
    folder, the place, each task, whether the terminal could say which sessions live (None when
    it could, else why not), the owner's presence, the backlog's read, the Inbox's record, the
    look at the forge, and whether the tasks are examples."""

    viewer: Viewer
    clock: Clock
    version: str
    place: Place
    tasks: tuple[Seen, ...]
    unknown: str | None = None
    presence: Presence = field(default_factory=Presence)
    backlog: Shelved | None = None
    inbox: Inbox | None = None
    forge: Forge = field(default_factory=Forge)
    demo: bool = False
