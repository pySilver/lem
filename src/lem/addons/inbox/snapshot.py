"""Translate the board's waits into one Inbox reconciliation."""

from typing import TYPE_CHECKING

from lem.addons.inbox import door, held, source
from lem.addons.inbox.live import live_of
from lem.addons.inbox.records import Look
from lem.model.owner import waiting
from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.app.owner.looking import Looked
    from lem.app.sessions.here import Here
    from lem.records.base import Moment


class Snapshot(Frozen, frozen=True, kw_only=True):
    """One look, its board rows and the live sessions for replies."""

    look: Look
    facts: tuple[source.RowFacts, ...]
    live: dict[str, str]


def gather(called: Here, seen: Looked, now: Moment) -> Snapshot:
    """Read the session ids once and use them for every part of the reconciliation."""
    sessions = live_of(called, seen)
    facts = source.facts(seen, sessions, now)
    return Snapshot(look=look_of(facts, seen, now), facts=facts, live=sessions)


def look_of(facts: tuple[source.RowFacts, ...], seen: Looked, now: Moment) -> Look:
    """Keep rows hidden by a stopped or currently active session in the record."""
    candidates = map(source.wait_of, facts)
    waits = tuple(wait for wait in candidates if wait is not None)
    present = waiting.rows(seen.looks, away=seen.presence.away, now=now)
    return Look(
        away=seen.presence.away,
        door=door.status(),
        waits=waits,
        behind=frozenset(row.key for row in present) - {wait.key for wait in waits},
        held=held.keys(seen),
    )
