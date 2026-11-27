"""A wake the server owes a task's session, sent once: whether a session of the task was woken
or opened since a moment, and the wake itself, which `lem session wake` makes (`waking.wake`),
with its failure kept so that it waits `memory.RETRY` (`serve.run_duties` on `main`).

The server never types into a session, never selects one and never closes one: a wake is a
pane message, and with no live session it opens one with no focus.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import log, waking
from lem.app.sessions.acts import Open, Wake
from lem.kernel.errors import Fault, Refusal
from lem.ports.terminal import Unreadable

if TYPE_CHECKING:
    from collections.abc import Collection
    from datetime import datetime

    from lem.app.sessions.acts import WakeWhy
    from lem.board.duties.context import Duty

# The problem of the board that the look at the sessions leaves.
SESSIONS = "sessions"


def known(duty: Duty) -> bool:
    """Whether the terminal says which sessions live now; while it cannot, the board shows
    why, and no duty that reads the sessions acts."""
    panes = duty.here.ports.terminal.sessions()
    if isinstance(panes, Unreadable):
        why = f"agterm's sessions could not be read: {panes.why}"
        duty.kept.problems[SESSIONS] = (
            f"the board's look at the task sessions failed: {why}"
        )
        return False
    duty.kept.problems.pop(SESSIONS, None)
    return True


def since(duty: Duty, slug: str, moment: datetime, whys: Collection[str] = ()) -> bool:
    """Whether a session of the task was woken or opened after `moment`, for one of `whys`
    when they are named."""
    acts = log.read(duty.here.folder(slug))
    reached = [act for act in acts if isinstance(act, Open | Wake)]
    later = [act for act in reached if act.at > moment]
    return any(not whys or act.why in whys for act in later)


def for_head(duty: Duty, slug: str, why: WakeWhy, head: str) -> bool:
    """Whether a wake for `why` of the task's session named the commit `head`."""
    acts = log.read(duty.here.folder(slug))
    named = {(act.why, act.head) for act in acts if isinstance(act, Wake)}
    return (why, head) in named


def after_end(duty: Duty, slug: str) -> bool:
    """Whether a session got the wake for this task's one end or opened after it."""
    reached = log.read(duty.here.folder(slug))
    session_acts = (act for act in reached if isinstance(act, Open | Wake))
    return any(act.after_end for act in session_acts)


def woken(
    duty: Duty,
    slug: str,
    why: WakeWhy,
    head: str | None = None,
) -> bool:
    """Wake the task's session for `why` unless that wake failed within the retry's wait; the
    wake's line, or why it failed, goes to the server's log."""
    key = ("wake", slug, why)
    if not duty.kept.due(key, duty.now):
        return False
    try:
        said = waking.wake(duty.here, slug, why, head, duty.now).say
    except (Refusal, Fault) as error:
        duty.kept.ended(key, duty.now, ran=False)
        duty.say(f"lem session wake {slug} --why {why} failed: {error}")
        return False
    duty.kept.ended(key, duty.now, ran=True)
    duty.say(f"lem session wake {slug} --why {why}: {said}")
    return True
