"""The word to the task's session after the owner's act on the board, which may wait for him:
`lem session wake SLUG --why owner`, a line to its live session, or a session opened when none
lives and the task needs one (`serve.tell_session` and `told_then` on `main`). What came of it is
a sentence of the act's note.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import here, waking
from lem.kernel.errors import Fault, Refusal

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path


def told(checkout: Path, slug: str, now: datetime, then: str) -> str:
    """Wake the task's session, and say what came of it and what the session does `then`."""
    try:
        woken = waking.wake(here.bound(checkout), slug, "owner", None, now)
    except (Refusal, Fault) as error:
        return (
            f"The task’s session was not told: {error}. Open a session of the task "
            f"here, and {then}."
        )
    if woken.woke:
        return f"The task’s session got word of it, and {then}."
    if woken.opened:
        return (
            "No session of the task ran: Lem opened one in agterm, at the end of its "
            f"workspace, and {then}."
        )
    return f"No session of the task runs, and none opens for it: {woken.say}."
