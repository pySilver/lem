"""The records and the live facts shared by a page and its version."""

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from lem.app.owner import looking, sessions
from lem.kernel import clock
from lem.model.owner.looks import MergeBasis

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.records.record import Record
    from lem.settings.effective import Effective


@dataclass(frozen=True, kw_only=True, slots=True)
class Snapshot:
    """The records and the live facts shared by a page and its version."""

    here: Here
    settings: Effective
    at: datetime
    records: tuple[Record, ...]
    listed: sessions.Listed | None
    unknown: str | None
    basis: MergeBasis

    def revision(self) -> str:
        """The session facts the views use, the reason they are unknown, and the base tree."""
        showed = self.listed or {}
        visible = tuple(
            (slug, sessions.session_of(entry, entry.since, None, known=True))
            for slug, entry in sorted(showed.items())
        )
        words = (visible, self.unknown, self.basis.tree)
        return repr(words) if any(words) else ""


def capture(
    here: Here, settings: Effective, records: tuple[Record, ...], *, demo: bool
) -> Snapshot:
    """Ask the terminal and git only for facts that a workspace page can display."""
    at = clock.now()
    listed, unknown = {}, None
    if not demo:
        listed, unknown = sessions.sessions_of(here, at, records)
    return Snapshot(
        here=here,
        settings=settings,
        at=at,
        records=records,
        listed=None if unknown else listed,
        unknown=unknown,
        basis=looking.basis_of(here, settings.branch, records),
    )


def with_files(
    found: Snapshot, settings: Effective, records: tuple[Record, ...]
) -> Snapshot:
    """Read a page with fresh files and the shared terminal and base facts."""
    branch = settings.branch
    tree = found.basis.tree if found.settings.branch.base == branch.base else None
    return replace(
        found,
        settings=settings,
        records=records,
        at=clock.now(),
        basis=MergeBasis(tree=tree, land=branch.land),
    )
