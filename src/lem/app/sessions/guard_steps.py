"""The guard's steps as commands, each in the task's lock (`session.lock`), after one more look
(`guard_acts.refusal`): `lem session wake --why status`, `lem session stopped`, `lem session
worked` and `lem session open --why stopped`."""

from typing import TYPE_CHECKING

from lem.app.sessions import beside, guard_look, log, opening
from lem.app.sessions.acts import Stopped, Wake, Worked
from lem.app.sessions.guard_acts import Acted, refusal, refused
from lem.kernel import locks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.guard_rule import Step
    from lem.app.sessions.here import Here


def stepped(
    here: Here, slug: str, step: Step, named: str | None, now: datetime
) -> Acted:
    """Take the guard's `step` for the task when it is still due, in the task's lock."""
    folder = here.folder(slug)
    with locks.held(folder / opening.LOCK):
        looked = guard_look.looked(here, slug, now)
        why = refusal(looked, step, named, now)
        if why is not None or looked.session is None:
            return refused(slug, looked.session, why or "gone")
        return dict(STEPS)[step](here, slug, looked, now)


def status(here: Here, slug: str, looked: guard_look.Looked, now: datetime) -> Acted:
    """Send `lem: SLUG status` to the live session, marked when its signs do not read."""
    session = looked.session or ""
    here.ports.terminal.tell(session, f"lem: {slug} status")
    unread = not looked.facts.read
    asked = Wake(at=now, session=session, why="status", unread=unread)
    log.append(here.folder(slug), asked)
    say = (
        f"the session of {slug} got `lem: {slug} status`, which asks where the task stands "
        "and to go on with its next step"
    )
    return Acted(task=slug, session=session, acted=True, say=say)


def stopped(here: Here, slug: str, looked: guard_look.Looked, now: datetime) -> Acted:
    """Put the stop on record: the task waits for the owner, whose open starts a fresh
    session."""
    session = looked.session or ""
    unread = not looked.facts.read
    stop = Stopped(at=now, session=session, unread=unread)
    log.append(here.folder(slug), stop)
    say = (
        f"the stop of {slug} is logged: its session showed no sign of work after the status "
        f"message, so it waits for the owner, whose lem session open {slug} --why stopped "
        "opens a fresh session"
    )
    return Acted(task=slug, session=session, acted=True, say=say)


def worked(here: Here, slug: str, looked: guard_look.Looked, now: datetime) -> Acted:
    """Put on record the turn the session took after an unread status message."""
    session = looked.session or ""
    turn = looked.facts.sign or now
    turned = Worked(at=now, session=session, turn=turn)
    log.append(here.folder(slug), turned)
    say = (
        f"the session of {slug} took a turn after the status message Lem sent while it could "
        "not read the session: no stop of the task waits for the owner"
    )
    return Acted(task=slug, session=session, acted=True, say=say)


def restart(here: Here, slug: str, looked: guard_look.Looked, now: datetime) -> Acted:
    """Open a fresh session beside the stopped one, name the old one `SLUG · replaced`, and
    tell it so."""
    old = looked.session or ""
    made = opening.opened_held(here, slug, "stopped", old, now)
    beside.looks(here.ports.terminal).rename(old, f"{slug} · replaced")
    here.ports.terminal.tell(old, f"lem: {slug} replaced")
    told = Wake(at=now, session=old, why="replaced")
    log.append(here.folder(slug), told)
    say = (
        f"{slug} goes on in a fresh session `{made.name}`, phase {made.phase}, beside the old "
        f"one, which is named `{slug} · replaced`"
    )
    return Acted(task=slug, session=old, acted=True, opened=made.session, say=say)


STEPS = (
    ("status", status),
    ("stopped", stopped),
    ("worked", worked),
    ("restart", restart),
)
