"""What the picker reads of the workspace: every task's record and the one list of what waits,
as `lem waiting` reads them. A record that does not read is named on standard error and counted
in the last row; with no record that reads, the picker refuses with their paths."""

from typing import TYPE_CHECKING

from lem.addons.picker import rows
from lem.app import task_reads
from lem.app.owner import looking
from lem.app.sessions import here as session_here
from lem.kernel.errors import Refusal
from lem.model.owner import waiting
from lem.settings.load import team_of

if TYPE_CHECKING:
    import datetime as dt
    from pathlib import Path

    from lem.model.owner.looks import Looks
    from lem.ports.terminal import PickRow


def listed(
    folder: Path, now: dt.datetime
) -> tuple[session_here.Here, tuple[PickRow, ...]]:
    """The workspace of `folder` and its rows; refused outside a repository of Lem and for one
    with no task yet."""
    here = session_here.bound(folder)
    checkout = here.where.checkout
    team_of(checkout)
    seen = looking.looked(here, now)
    task_reads.warned(seen.unread)
    waits = waiting.rows(seen.looks, away=seen.presence.away, now=now)
    found = rows.rows_of(records_of(seen.looks), waits, now, seen.unread)
    if not found:
        seen.require_complete()
        raise Refusal(
            "no-task",
            f"there is no task yet in {checkout}",
            "/lem and a request opens one",
        )
    return here, found


def records_of(found: Looks) -> rows.Records:
    """Each task's record by its slug."""
    return {look.record.task.slug: look.record for look in found}
