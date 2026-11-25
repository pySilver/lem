"""`lem session wait`: end when the task's status is one of those named, when a new entry of a
kind is put on its record, when its newest session is gone, with a companion when that companion
of the waiting session is gone, or with a quiet file when it has not changed for 45 minutes
(`session.cmd_wait` on `main`).

An entry's kind is the `kind` of the task's journal (`state`, `span`, `decision`, ...) or of an
act on its sessions (`open`, `wake`, ...); the wait counts them at its start and ends at the
first new one. A gone session ends the wait with `gone` and the line that opens a fresh one; a
terminal that does not answer one look is asked again at the next.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions import log, seen
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.records.base import Frozen, Moment
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here

# How long `--quiet FILE` waits with no change of FILE before it ends: 45 minutes, the guard's
# number for a session with no sign of work (the owner's, 2026-11-22), as a guess for a talk.
QUIET_SECONDS = 2700


class Waited(Frozen, frozen=True, kw_only=True):
    """Why the wait ended: the task's status and since when, the new entry, a session or a
    companion that is gone, a quiet file, and the line for the owner."""

    task: str
    status: str
    since: Moment
    gone: bool = False
    entry: msgspec.Raw | None = None
    session: str | None = None
    companion: str | None = None
    quiet: str | None = None
    say: str | None = None


def kinds(here: Here, slug: str) -> list[bytes]:
    """Every entry of the task's journal and of its sessions' acts, each as its JSON."""
    record = tasks.read(here.where.state, slug)
    acts = log.read(here.folder(slug))
    return [msgspec.json.encode(entry) for entry in (*record.journal, *acts)]


def entry_of(here: Here, slug: str, kind: str, seen_before: int) -> msgspec.Raw | None:
    """The first entry of `kind` after the first `seen_before` of that kind, or None."""
    mark = marked(kind)
    found = [one for one in kinds(here, slug) if mark in one]
    return msgspec.Raw(found[seen_before]) if len(found) > seen_before else None


def counted(here: Here, slug: str, kind: str | None) -> int:
    """How many entries of `kind` the task has now."""
    if kind is None:
        return 0
    mark = marked(kind)
    return sum(mark in one for one in kinds(here, slug))


def marked(kind: str) -> bytes:
    """The bytes that open an entry of `kind` in its JSON."""
    return b"".join((b'"kind":', msgspec.json.encode(kind)))


def gone_session(here: Here, slug: str, now: datetime) -> str | None:
    """The task's newest session when it no longer carries the task; None while it does,
    while none is on record, or when the terminal did not answer."""
    newest = log.newest_open(log.read(here.folder(slug)))
    if newest is None:
        return None
    try:
        carried = seen.look(here).carries(newest, now)
    except Refusal, Unanswered:
        return None
    return None if carried else newest.session


def gone_companion(here: Here, companion: str) -> bool:
    """Whether the companion `companion` of the waiting session is gone from the terminal;
    False when the terminal did not answer."""
    try:
        return seen.look(here).pane(companion) is None
    except Refusal, Unanswered:
        return False
