"""`lem session next`: the change of phase, a fresh session for the phase the task's record now
gives, after the leaving agent wrote its record and `handoff.md`.

The phase that ends is the record's, never only the one the newest session opened in: of the
state entries the journal holds since that session opened, the newest before the run that gives
the phase the task is in now, else the phase it opened in, so a session that led its task from
the shape through the build hands off from the build (`session.phase_left` on `main`). It
refuses while the record still gives that phase, unless `same` (the owner's "hand off" inside a
phase); and a `handoff.md` that is not in its form, not from the phase that ends, or older than
that session. The session that leaves is the caller's, else the task's newest; it is named
`SLUG · handed off`, and the line that closes it once the owner has left it is given for the
leaving agent to run in the background. When another session of the task runs already, which
took the task over, it refuses.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions import handoff, log, opening, queued
from lem.app.sessions.phase import Phase, phase_noted
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.records.journal.task import StateNoted
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.acts import Open
    from lem.app.sessions.here import Here
    from lem.records.record import Record


class Handed(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The fresh session, the old one, the phase that ended, and the old one's close."""

    task: str
    session: str
    name: str
    phase: Phase
    workspace: str | None
    old: str
    ended: str = msgspec.field(name="from")
    close: str


def hand_on(here: Here, slug: str, *, same: bool, now: datetime) -> Handed:
    """Open the session of the next phase, or a fresh one of the same phase when `same`."""
    newest = newest_of(here, slug)
    ended = ending(here, slug, newest, same=same)
    handoff.checked(here.folder(slug), slug, ended, newest.at)
    old = here.caller or newest.session
    made = opening.open_session(here, slug, "handoff", old, now)
    return handed(here, made, old, ended)


def newest_of(here: Here, slug: str) -> Open:
    """The task's newest session; refused when Lem opened none."""
    newest = log.newest_open(log.read(here.folder(slug)))
    if newest is None:
        raise Refusal(
            "no-session",
            f"no session of {slug} is on record, so there is no phase to hand off",
            f"lem session open {slug} opens its first",
        )
    return newest


def handed(here: Here, made: opening.Opened, old: str, ended: str) -> Handed:
    """Name the old session handed off, and give the change; refused when another session of
    the task took it over."""
    slug = made.task
    close = f"lem session close {slug} --session {old} --why handoff --when-unselected"
    if made.already:
        raise Refusal(
            "taken-over",
            f"another session of {slug} runs already, {made.name} ({made.session})",
            f"this one closes with {close}",
        )
    here.ports.terminal.rename(old, f"{slug} · handed off")
    return Handed(
        task=slug,
        session=made.session,
        name=made.name,
        phase=made.phase,
        workspace=made.workspace,
        old=old,
        ended=ended,
        close=close,
    )


def ending(here: Here, slug: str, newest: Open, *, same: bool) -> str:
    """The phase that ends; refused while the record still gives it."""
    record = tasks.read(here.where.state, slug)
    queued.release_stop(record.task)
    now = here.phase(record.task)
    if same:
        return now
    ended = left_by(record, newest.at, now) or newest.phase
    if ended == now:
        raise Refusal(
            "same-phase",
            f"the record of {slug} still gives the phase {now}",
            "write the record that ends the phase first, then run this again; for the "
            f"owner's hand off inside a phase, lem session next {slug} --same",
        )
    return ended


def left_by(record: Record, since: datetime, now: str) -> str | None:
    """The phase of the newest state entry since `since` that gives another phase than
    `now`, the one the task is in."""
    noted = [entry for entry in record.journal if isinstance(entry, StateNoted)]
    newer = (entry for entry in reversed(noted) if entry.at >= since)
    phases = (phase_noted(record.task, entry.status, entry.hold) for entry in newer)
    return next((phase for phase in phases if phase not in {None, now}), None)
