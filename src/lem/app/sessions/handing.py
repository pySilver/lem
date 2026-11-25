"""`lem session next`: the change of phase, a fresh session for the phase the task's record now
gives, after the leaving agent wrote its record and `handoff.md`.

It refuses while the record still gives the phase the newest session opened in, unless `same`
(the owner's "hand off" inside a phase); and a `handoff.md` that is not in its form, not from the
phase that ends, or older than that session. It gives the line that closes the old session once
the owner has left it, which the leaving agent runs in the background.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions import handoff, opened, opening
from lem.app.sessions.phase import Phase
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from lem.app.sessions.here import Here


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
    folder = here.folder(slug)
    newest = opened.newest_open(opened.read(folder))
    if newest is None:
        raise Refusal(
            "no-session",
            f"no session of {slug} is on record, so there is no phase to hand off",
            f"lem session open {slug} opens its first",
        )
    phase = here.phase(tasks.read(here.where.state, slug).task)
    ended = phase if same else newest.phase
    if phase == ended and not same:
        raise Refusal(
            "same-phase",
            f"the record of {slug} still gives the phase {ended}",
            "write the record that ends the phase first, then run this again; for the "
            f"owner's hand off inside a phase, lem session next {slug} --same",
        )
    checked(folder, slug, ended, newest.at)
    made = opening.open_session(here, slug, "handoff", newest.session, now)
    return handed(made, newest.session, ended)


def checked(folder: Path, slug: str, ended: str, opened_at: datetime) -> None:
    """Refuse a `handoff.md` that is missing, not in its form, from another phase than
    `ended`, or written before the session that leaves opened."""
    path = folder / handoff.HANDOFF
    if not path.is_file():
        raise Refusal(
            "no-handoff",
            f"{path} is not there",
            "write the handoff in the form of `templates/handoff.md` first",
        )
    found = handoff.form(path.read_text(encoding="utf-8"), slug)
    if found.phase != ended:
        raise Refusal(
            "handoff-phase",
            f"{handoff.HANDOFF} of {slug} is from {found.phase}, and the phase that ends is "
            f"{ended}",
            "write it again for the phase that ends",
        )
    if found.written < opened_at.replace(second=0):
        raise Refusal(
            "handoff-old",
            f"{handoff.HANDOFF} of {slug} was written before this session opened: it is "
            "an older session's",
            "write it again",
        )


def handed(made: opening.Opened, old: str, ended: str) -> Handed:
    """The outcome of a change of phase; refused when another session took the task over."""
    slug = made.task
    if made.already:
        raise Refusal(
            "taken-over",
            f"another session of {slug} runs already, {made.name} ({made.session})",
            f"this one closes with lem session close {slug} --session {old} --why handoff "
            "--when-unselected",
        )
    return Handed(
        task=slug,
        session=made.session,
        name=made.name,
        phase=made.phase,
        workspace=made.workspace,
        old=old,
        ended=ended,
        close=f"lem session close {slug} --session {old} --why handoff --when-unselected",
    )
