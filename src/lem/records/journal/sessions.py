"""The journal's entries of Lem's acts on a task's sessions: an open, a close, a wake, the
guard's stop, and a turn it saw after a status message it sent while it could not read the
session (`main`'s `session.open`, `session.close`, `session.wake`, `session.stopped`,
`session.worked`). Each names the terminal's session."""

from typing import Literal

from lem.records.base import Moment, Tagged

type CloseWhy = Literal["handoff", "ended", "owner"]
type WakeWhy = Literal[
    "merged", "conflict", "refused", "queue", "owner", "inbox", "status", "replaced"
]


class SessionOpened(Tagged, tag="session-open", frozen=True, kw_only=True):
    """A session Lem opened for the task: its name, the phase it opened in, why, and the
    terminal's workspace it went into, None when it was the caller's."""

    at: Moment
    session: str
    name: str
    phase: str
    why: str
    workspace: str | None = None


class SessionClosed(Tagged, tag="session-close", frozen=True, kw_only=True):
    """A session of the task that Lem closed, or found gone, and why."""

    at: Moment
    session: str
    why: CloseWhy


class SessionWoken(Tagged, tag="session-wake", frozen=True, kw_only=True):
    """A line `lem: SLUG WHY` that Lem sent to the session; the pull request's head it was
    for, and whether the session's signs did not read when the guard sent it (`unread`)."""

    at: Moment
    session: str
    why: WakeWhy
    head: str | None = None
    unread: bool = False


class SessionStopped(Tagged, tag="session-stopped", frozen=True, kw_only=True):
    """The guard's stop: the session showed no sign of work after its status message (and
    its restart), so the task waits for the owner; `unread` when its signs did not read."""

    at: Moment
    session: str
    unread: bool = False


class SessionWorked(Tagged, tag="session-worked", frozen=True, kw_only=True):
    """A turn of the session, at `turn`, that a look which read its signs saw after a status
    message Lem sent while it could not read them."""

    at: Moment
    session: str
    turn: Moment
