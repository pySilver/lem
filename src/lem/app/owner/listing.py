"""`lem waiting`: everything that waits for the owner, from the records that hold it; nothing
here decides or writes (`project.cmd_waiting` on `main`).

Its rows are the rows of the board's "Waits for you", so that the terminal and the phone list the
same; each group holds the rows of one kind, `tasks` the same rows grouped by task as the board's
stacks, and `count` the tasks that wait. With a task named, only that task's.
"""

from datetime import timedelta
from typing import TYPE_CHECKING

from lem.app.owner import looking, scope, stacks
from lem.app.owner.listed import ForgeSeen, Known, NightReport, OwnerNow, Waiting
from lem.app.sessions import here as session_here
from lem.settings.load import settings_of
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import date, datetime
    from pathlib import Path

    from lem.records.owner import Presence

NIGHTS = "night"


def listed(folder: Path, slug: str | None, now: datetime, today: date) -> Waiting:
    """What waits for the owner in the workspace of `folder`, or for its task `slug`."""
    here = session_here.bound(folder)
    settings_of(here.where.checkout, git=here.ports.git, home=here.home)
    if slug is not None:
        tasks.read(here.where.state, slug)
    seen = looking.looked(here, now)
    mine = scope.scoped(seen, slug, now)
    stacked = stacks.stacked(mine)
    return Waiting(
        owner=owner_now(seen.presence),
        breakers=scope.breakers(mine),
        rows=stacks.keyed(mine),
        tasks=stacked,
        sessions=Known(known=seen.unknown is None, said=seen.unknown),
        forge=ForgeSeen(looked=seen.forge.looked),
        night_report=night_report(here.where.state, today),
        parked=stacks.parked(mine),
        count=len(stacked),
        **scope.grouped(mine),
    )


def owner_now(presence: Presence) -> OwnerNow:
    """Whether he is away, since when, in which words, and the count of his mark."""
    return OwnerNow(
        away=presence.away,
        since=presence.since,
        words=presence.words,
        seen=presence.seen,
    )


def night_report(state: Path, today: date) -> NightReport | None:
    """The report of last night: a night writes it under the day it started, so today's or
    yesterday's, by the local day."""
    for day in (today, today - timedelta(days=1)):
        path = state / NIGHTS / f"{day.isoformat()}.md"
        if path.is_file():
            return NightReport(date=day, path=str(path))
    return None
