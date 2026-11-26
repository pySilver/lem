"""The records and the live facts shared by a page and its version."""

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from lem.app.owner import merge_bases, sessions
from lem.kernel import clock

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.settings.effective import Effective
    from lem.store.survey import Survey


@dataclass(frozen=True, kw_only=True, slots=True)
class Snapshot:
    """The records and the live facts shared by a page and its version."""

    here: Here
    settings: Effective
    at: datetime
    read: Survey
    listed: sessions.Listed | None
    unknown: str | None
    bases: merge_bases.Bases

    def revision(self) -> str:
        """The session facts the views use, the reason they are unknown, and the base tree."""
        showed = self.listed or {}
        visible = tuple(
            (slug, sessions.session_of(entry, entry.since, None, known=True))
            for slug, entry in sorted(showed.items())
        )
        refs = tuple(sorted(self.bases.refs.items()))
        if visible or self.unknown or refs:
            return repr((visible, self.unknown, refs))
        return ""


def capture(here: Here, settings: Effective, read: Survey, *, demo: bool) -> Snapshot:
    """Ask the terminal and git only for facts that a workspace page can display."""
    at = clock.now()
    listed, unknown = sessions.sessions_of(here, at, read.readable, demo=demo)
    return Snapshot(
        here=here,
        settings=settings,
        at=at,
        read=read,
        listed=None if unknown else listed,
        unknown=unknown,
        bases=merge_bases.gathered(here, settings.branch, read.readable),
    )


def with_files(found: Snapshot, settings: Effective, read: Survey) -> Snapshot:
    """Read a page with fresh files and the shared terminal and base facts."""
    return replace(
        found,
        settings=settings,
        read=read,
        at=clock.now(),
        bases=replace(found.bases, settings=settings.branch),
    )
