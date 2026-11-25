"""A duty of the board server: the guard of a stopped session (`wake … status`,
`open … stopped`, `stopped … stopped` and `worked … worked` of `serve.duties` on `main`).

For each task the guard watches (building, ready or landing, with no hold) the rule of
`app/sessions/guard_rule.py` gives the step due now: the status message after 45 minutes with
no sign of work (by the task's own work when the session's signs do not read), a fresh session
10 minutes after it when the signs read, else the stop, once, which the owner's "Waits for you"
shows; and the turn the session took after a message sent while its signs did not read. The
step names the session it is for, and looks once more in the task's lock before it acts
(`guard_steps.stepped`): one that acts on nothing says why, and the next tick asks again.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.owner import releases
from lem.app.sessions import guard_look, guard_steps
from lem.app.sessions.guard_due import due
from lem.app.sessions.guard_rule import GUARDED
from lem.board.duties import wakes
from lem.kernel.errors import Fault, Refusal
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.sessions.guard_rule import Step
    from lem.board.duties.context import Duty

# Each step as the command of `lem session` that takes it, for the server's log.
WORDS = MappingProxyType(
    {
        "status": "wake {slug} --why status",
        "restart": "open {slug} --why stopped",
        "stopped": "stopped {slug}",
        "worked": "worked {slug}",
    }
)


def tick(duty: Duty) -> None:
    """Take the step due for each task the guard watches."""
    records = releases.with_stops(tasks.every(duty.state))
    watched = [one.task.slug for one in records if one.task.status in GUARDED]
    held = {one.task.slug for one in records if one.task.hold is not None}
    slugs = [slug for slug in watched if slug not in held]
    if slugs and wakes.known(duty):
        for slug in slugs:
            guarded(duty, slug)


def guarded(duty: Duty, slug: str) -> None:
    """Take the step due for the task now, for its newest session, unless that step failed
    within the retry's wait."""
    looked = guard_look.looked(duty.here, slug, duty.now)
    found = due(looked.line, looked.facts, duty.now)
    if found is None or looked.session is None:
        return
    key = ("guard", slug, found.step)
    if duty.kept.due(key, duty.now):
        stepped(duty, slug, found.step, looked.session)


def stepped(duty: Duty, slug: str, step: Step, session: str) -> None:
    """Take the step for the session `session`, and say in the server's log what it did."""
    command = WORDS[step].format(slug=slug)
    words = f"lem session {command} --session {session}"
    key = ("guard", slug, step)
    try:
        acted = guard_steps.stepped(duty.here, slug, step, session, duty.now)
    except (Refusal, Fault) as error:
        duty.kept.ended(key, duty.now, ran=False)
        duty.say(f"{words} failed: {error}")
        return
    duty.kept.ended(key, duty.now, ran=True)
    duty.say(f"{words}: {acted.say}")
