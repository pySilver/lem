"""What the list of what waits for the owner reads of each task, and its rows (`board_model.Model`
and `waits_of` on `main`).

A task's record says most of it; the rest is a look at the world that `app/owner` gathers once:
the task's newest session as the terminal shows it, the guard's stop that stands, whether its
worktree is there, and whether the forge calls its pull request conflicting. A row is one thing
the owner does, with its kind, its key, its task and the moment it began to wait.
"""

from typing import Literal

from lem.records.base import Frozen, Moment, Sha, Slug
from lem.records.record import Record

type Kind = Literal[
    "breaker",
    "session",
    "stopped",
    "criteria",
    "held",
    "card",
    "after_dropped",
    "blocked",
    "plan",
    "review",
    "merge",
]


class Session(Frozen, frozen=True, kw_only=True):
    """The task's newest session: whether its pane has its agent, when it opened, whether
    it left the newest wake-up unanswered, and whether its newest turn runs."""

    live: bool
    since: Moment
    unanswered: bool = False
    working: bool = False


class Stop(Frozen, frozen=True, kw_only=True):
    """The guard's stop that stands over a task whose session lives: when, whether Lem could
    not read the session, and whether a fresh session took the stopped one's place first."""

    at: Moment
    unread: bool = False
    restarted: bool = True


class Look(Frozen, frozen=True, kw_only=True):
    """One task as the list reads it: its record and the look at the world."""

    record: Record
    session: Session | None = None
    stop: Stop | None = None
    worktree: bool = False
    conflict: bool = False


class Row(Frozen, frozen=True, kw_only=True):
    """One thing that waits for the owner: its kind, its key (the board's, the pushes' and the
    Inbox's), its task, and since when; then the facts of its kind."""

    kind: Kind
    key: str
    task: Slug
    since: Moment
    deaf: bool = False
    unread: bool = False
    restarted: bool = True
    after: Slug | None = None
    say: str | None = None
    card: str | None = None
    prompt: str | None = None
    why: str | None = None
    tip: Sha | None = None
    conflict: bool = False


type Rows = tuple[Row, ...]
type Looks = tuple[Look, ...]
