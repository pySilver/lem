"""What the picker reads of the workspace: every task's record and the one list of what waits,
as `lem waiting` reads them."""

from typing import TYPE_CHECKING

from lem.addons.picker import rows
from lem.app.owner import looking
from lem.app.sessions import here as session_here
from lem.kernel.errors import Refusal
from lem.model.owner import waiting
from lem.settings.load import team_of

if TYPE_CHECKING:
    import datetime as dt
    from pathlib import Path

    from lem.addons.picker.row import PickRow
    from lem.app.sessions.here import Here
    from lem.model.owner.looks import Looks


def listed(folder: Path, now: dt.datetime) -> tuple[Here, tuple[PickRow, ...]]:
    """The workspace of `folder` and its rows; refused outside a repository of Lem and for one
    with no task yet."""
    here = session_here.bound(folder)
    checkout = here.where.checkout
    team_of(checkout)
    seen = looking.looked(here, now)
    waits = waiting.rows(seen.looks, away=seen.presence.away, now=now)
    found = rows.rows_of(records_of(seen.looks), waits, now)
    if not found:
        raise Refusal(
            "no-task",
            f"there is no task yet in {checkout}",
            "/lem and a request opens one",
        )
    return here, found


def records_of(found: Looks) -> rows.Records:
    """Each task's record by its slug."""
    return {look.record.task.slug: look.record for look in found}
