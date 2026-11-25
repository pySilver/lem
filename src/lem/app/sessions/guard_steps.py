"""The guard's steps as commands, each in the task's lock (`session.lock`), after one more look
(`guard_acts.refusal`): `lem session wake --why status`, `lem session stopped`, `lem session
worked` and `lem session open --why stopped`."""

from typing import TYPE_CHECKING

from lem.app.sessions import beside, guard_look, guard_stop, log, opening
from lem.app.sessions.acts import Wake, Worked
from lem.app.sessions.guard_acts import Acted, refusal, refused
from lem.kernel import locks
from lem.ports.faults import Unanswered

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
    log.reached(here.folder(slug), asked)
    say = (
        f"the session of {slug} got `lem: {slug} status`, which asks where the task stands "
        "and to go on with its next step"
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
    """Open a fresh session beside the stopped one, then name the old one `SLUG · replaced`
    and tell it so; the fresh session is on record first, and what fails after it is said,
    never raised (`session.tell_replaced` on `main`)."""
    old = looked.session or ""
    made = opening.opened_held(here, slug, "stopped", old, now)
    problem = replaced(here, slug, old, now)
    say = (
        f"{slug} goes on in a fresh session `{made.name}`, phase {made.phase}, beside the old "
        f"one, which is named `{slug} · replaced`"
    )
    told = problem is None
    return Acted(
        task=slug,
        session=old,
        acted=True,
        opened=made.session,
        told=told,
        problem=problem,
        say=say,
    )


def replaced(here: Here, slug: str, old: str, now: datetime) -> str | None:
    """Name the old session replaced and send it the line, put on record as its wake; what
    the terminal answered when it failed, else None."""
    try:
        tell_replaced(here, slug, old)
    except Unanswered as unanswered:
        return str(unanswered)
    told = Wake(at=now, session=old, why="replaced")
    log.reached(here.folder(slug), told)
    return None


def tell_replaced(here: Here, slug: str, old: str) -> None:
    """Name the old session `SLUG · replaced`, and send it `lem: SLUG replaced`."""
    beside.looks(here.ports.terminal).rename(old, f"{slug} · replaced")
    here.ports.terminal.tell(old, f"lem: {slug} replaced")


STEPS = (
    ("status", status),
    ("stopped", guard_stop.stopped),
    ("worked", worked),
    ("restart", restart),
)
