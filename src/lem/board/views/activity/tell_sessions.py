"""The feed's words of Lem's acts on a task's sessions: an open, a close, a wake, a turn the guard
saw, and its stop (`session.open`, `session.close`, `session.wake`, `session.worked` and
`session.stopped` of `main`'s `SAYS`)."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.sessions.acts import Close, Open, Stopped, Wake
from lem.app.sessions.guard_rule import QUIET_SECONDS
from lem.board.views.activity import stops
from lem.board.views.activity.told import LEM, QUIET, SPLIT, Told

if TYPE_CHECKING:
    from lem.app.sessions.acts import Act
    from lem.app.sessions.guard_rule import Timeline

QUIET_MINUTES = QUIET_SECONDS // 60
CLOSED = MappingProxyType(
    {
        "handoff": "a fresh session took its place",
        "ended": "the task ended",
        "owner": "you closed it",
    }
)
OPENED = MappingProxyType(
    {
        "new": "for a new task",
        "handoff": "for the next phase",
        "dead": "in place of one that was gone",
        "merged": "after the merge, for the cleanup",
        "conflict": "to bring its pull request onto the base",
        "queue": "the task it waited for ended",
        "night": "for the night",
        "owner": "on your word",
        "stopped": (
            "beside the one that stopped, whose name in agterm now ends in “replaced”"
        ),
    }
)
WOKEN = MappingProxyType(
    {
        "merged": "the pull request is merged: the session cleans up",
        "conflict": (
            "GitHub calls the pull request conflicting: the session brings it onto the base"
        ),
        "queue": "the task it waited for ended",
    }
)
WORKED = Told(
    LEM,
    SPLIT,
    "Lem read the task’s session again, and it worked",
    (
        "a turn of the session came after the status message that Lem sent while it could "
        "not read it, so no stop waits for you"
    ),
)


def act(done: Act, line: Timeline) -> Told:
    """One act on the task's sessions in words."""
    match done:
        case Open():
            return opened(done)
        case Close():
            closed = CLOSED.get(done.why, done.why)
            return Told(QUIET, SPLIT, "A session of the task closed", closed)
        case Wake():
            return woken(done)
        case Stopped():
            return stops.stopped(done, line)
        case _:
            return WORKED


def opened(done: Open) -> Told:
    """A session Lem opened: its name, its phase and why; a fresh one in a stopped one's place
    says that it took the task over."""
    phase = f"the {done.phase} phase" if done.phase else ""
    why = OPENED.get(done.why, done.why)
    sub = " · ".join(part for part in (phase, why) if part)
    if done.why == "stopped":
        return Told(LEM, SPLIT, "A fresh session took the task over", done.name, sub)
    return Told(LEM, SPLIT, "The task’s session opened", done.name, sub)


def woken(done: Wake) -> Told:
    """A line Lem sent to the session: the guard's status message, the notice to an old session
    that a fresh one replaced it, or a wake with its reason."""
    if done.why == "status":
        return status(unread=done.unread)
    if done.why == "replaced":
        return Told(
            QUIET,
            SPLIT,
            "The board’s server told the old session that a fresh one replaced it",
            "it closes itself at the end of its turn",
        )
    said = WOKEN.get(done.why, done.why)
    return Told(LEM, SPLIT, "The board’s server woke the task’s session", said)


def status(*, unread: bool) -> Told:
    """The guard's status message, after a quiet it could read or one it could not."""
    if unread:
        quiet = (
            f"no event of the task for {QUIET_MINUTES} minutes, and Lem cannot read its "
            "session"
        )
    else:
        quiet = f"no sign of work for {QUIET_MINUTES} minutes"
    said = f"{quiet}: it says where the task stands and goes on with its next step"
    head = "The board’s server asked the task’s session for its status"
    return Told(LEM, SPLIT, head, said)
