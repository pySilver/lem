"""The four acts of the guard of a stopped session, each after one more look in the task's lock
(`session.guard_check` on `main`): the status message (`wake --why status`), the restart beside
the stopped session (`open --why stopped`), the stop (`stopped`) and the turn after an unread
status message (`worked`).

Each acts only when the guard still watches the task, its newest session is the one named and
still lives with an agent in its pane, no shell command of it runs, and the rule still gives
that step; else it acts on nothing and says why, and the board server's next look asks again.
A restart that names no session is the owner's "Open a session" on a stopped task: it acts while
the stop stands and, when the signs read, no sign of work came after it. A restart that names
one is the server's duty, which never acts over a stop that stands, nor beside a session whose
signs do not read.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.sessions import log
from lem.app.sessions.guard_due import due
from lem.records.base import Frozen

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.guard_look import Looked
    from lem.app.sessions.guard_rule import Step

WORKING = "working"
# Why a step acted on nothing, each with its words (`session.REFUSALS` on `main`).
REFUSALS = MappingProxyType(
    {
        WORKING: (
            "its session showed a sign of work since the step was due, or a shell command of "
            "it runs, or the step was taken already"
        ),
        "status": "the task is no longer in building, ready or landing with no hold",
        "gone": (
            "the session the step was for is not the task's newest any more, or it no longer "
            "lives in agterm with an agent"
        ),
        "unread": (
            "its session's signs of work do not read, and Lem opens a fresh session beside "
            'such a session only on the owner\'s "Open a session" over its logged stop'
        ),
    }
)


class Acted(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """A step of the guard: the task, the session it was for, whether it acted, why not, the
    fresh session of a restart, and the line for the owner."""

    task: str
    session: str | None
    acted: bool
    why: str | None = None
    opened: str | None = None
    say: str


def refused(slug: str, session: str | None, why: str) -> Acted:
    """The step that acted on nothing, and why."""
    say = f"Lem did nothing for {slug}: {REFUSALS[why]}; the board server's next look asks again"
    return Acted(task=slug, session=session, acted=False, why=why, say=say)


def refusal(looked: Looked, step: Step, named: str | None, now: datetime) -> str | None:
    """Why the step acts on nothing now, a key of REFUSALS, or None when it acts."""
    facts = looked.facts
    if not facts.guarded:
        return "status"
    other = named is not None and not log.same(named, looked.session)
    if not facts.alive or other:
        return "gone"
    if facts.shell:
        return WORKING
    if step == "restart":
        return restart_refusal(looked, named, now)
    found = due(looked.line, facts, now)
    return None if found is not None and found.step == step else WORKING


def restart_refusal(looked: Looked, named: str | None, now: datetime) -> str | None:
    """Why a restart acts on nothing: the owner's own acts over a stop that stands, the
    server's never over one, nor beside signs that do not read."""
    facts = looked.facts
    stop = looked.line.stop_stands()
    if stop is not None and named is None:
        stopped = looked.line.events[stop].at
        newer = facts.read and facts.sign is not None and facts.sign > stopped
        return WORKING if newer else None
    if not facts.read:
        return "unread"
    found = due(looked.line, facts, now)
    return None if found is not None and found.step == "restart" else WORKING
