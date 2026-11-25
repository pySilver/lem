"""What the views of a workspace read: each task's record and what lies beside it, the owner's
presence, the tasks' sessions as the terminal showed them, the backlog, the Inbox's record, the
look at the forge, and who asks for the page at what minute.

A view is a pure function of this value: `gather.py` reads it from a workspace once for a page,
and a test builds it from the records it holds.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.app.sessions.acts import Act
from lem.board import merge_look
from lem.board.views import facts
from lem.model.owner.looks import Look, MergeBasis, Session, Stop
from lem.records import base, owner, record

if TYPE_CHECKING:
    from datetime import datetime, tzinfo

    from lem.board.inputs.layout import Viewer
    from lem.board.inputs.task.head import Fact
    from lem.board.views import backlog_read, inbox_read
    from lem.settings.team import History


class Seen(base.Frozen, frozen=True, kw_only=True):
    """A task's record and what lies beside it: Lem's acts on its sessions, the files of its
    folder, the size and time of each, their text and the worktree plan, the newest commit of
    its branch, the backlog items its branch
    adds (None when git cannot tell), whether its worktree is there, its live session as the
    terminal shows it, the guard's stop that stands over it, and whether it runs without the
    owner now (he is away, or the night opened it)."""

    record: record.Record
    acts: tuple[Act, ...] = ()
    files: tuple[str, ...] = ()
    prose: tuple[tuple[str, str], ...] = ()
    plan_file: facts.PlanFile | None = None
    stats: tuple[facts.Stat, ...] = ()
    head: facts.Commit | None = None
    filed: tuple[facts.Filed, ...] | None = None
    worktree: bool = False
    session: Session | None = None
    stop: Stop | None = None
    alone: bool = False

    basis: MergeBasis = MergeBasis()

    def merge_look(self) -> Look:
        """The record and the base its merge review must cover."""
        return merge_look.look(self.record, self.basis)

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
    its main checkout, its backlog folder, and how its branches land."""

    repo: str
    base: str
    path: str
    backlog: str = "docs/backlog"
    history: History = "squash"


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
    presence: owner.Presence = field(default_factory=owner.Presence)
    backlog: backlog_read.Shelved | None = None
    inbox_thread: Fact | None = None
    inbox: inbox_read.Inbox | None = None
    forge: Forge = field(default_factory=Forge)
    problems: tuple[str, ...] = ()
    running: frozenset[str] = frozenset()
    demo: bool = False
