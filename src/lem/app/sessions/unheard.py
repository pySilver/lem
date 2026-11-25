"""Whether the newest wake of a live session went unanswered, and how (`session.unheard_of` on
`main`).

A wake older than UNANSWERED_AFTER is unanswered when its line still waits in the session's
mailbox (`waits`), or when the session's signs read and show no turn since the wake: `runs`
while its newest turn or a shell command of it runs (Claude Code queues a line that comes during
a turn), `taken` when neither does (a parked Claude Code process takes the line out of its
mailbox with no turn, merge-leaves-board-lock, 2026-11-22). A turn in the same second as the
wake counts as after it. The guard's own status message is never one: the guard ends its wait
with the restart or the stop.
"""

from typing import TYPE_CHECKING, Literal

from lem.app.sessions import beside, log
from lem.app.sessions.acts import Wake
from lem.records.base import Frozen

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.app.sessions.signs import Read

# After how long a wake that no turn followed is unanswered: 10 minutes, a guess
# (`session.UNANSWERED_AFTER` on `main`).
UNANSWERED_AFTER = 600


class Unheard(Frozen, frozen=True, kw_only=True):
    """The wake's why, and what became of its line."""

    why: str
    line: Literal["waits", "runs", "taken"]


def unheard_of(
    here: Here, slug: str, session: str, signs: Read, now: datetime
) -> Unheard | None:
    """How the newest wake of the session went unanswered, or None."""
    wake = newest_wake(here, slug, session)
    if wake is None or wake.why == "status":
        return None
    if (now - wake.at).total_seconds() < UNANSWERED_AFTER:
        return None
    line = f"lem: {slug} {wake.why}"
    if beside.looks(here.ports.terminal).waiting(session, line):
        return Unheard(why=wake.why, line="waits")
    return taken(wake, signs)


def taken(wake: Wake, signs: Read) -> Unheard | None:
    """The wake's line taken with no turn since, when the signs read and say so."""
    answered = signs.sign is not None and signs.sign >= wake.at
    if not signs.signs or answered:
        return None
    busy = signs.turn == "runs" or signs.shell
    return Unheard(why=wake.why, line="runs" if busy else "taken")


def newest_wake(here: Here, slug: str, session: str) -> Wake | None:
    """The newest wake Lem sent to the session."""
    acts = log.of_session(log.read(here.folder(slug)), session)
    wakes = [act for act in acts if isinstance(act, Wake)]
    return wakes[-1] if wakes else None
