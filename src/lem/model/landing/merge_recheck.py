"""An approval on a moved base waits for checks on the rebased change."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing.world import Due
from lem.records.landing.merge import Refused

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.journal.landing import CheckEnd
    from lem.records.landing.checks import Checked
    from lem.records.landing.record import Landing
    from lem.records.record import Record


def moved(landing: Landing | None, base: str) -> bool:
    """The base commit has changed since the last run of the checks."""
    checked = landing.checked if landing else None
    return checked is not None and checked.base != base


def priority(record: Record, base: str | None) -> bool:
    """Sort a passed run on the current base ahead of work that needs new checks."""
    checked = record.landing.checked if record.landing else None
    return checked is None or checked.outcome != "passed" or checked.base != base


def refusal(record: Record, world: World) -> Refusal | None:
    """Why an approved merge may not use checks from another base commit."""
    if not moved(record.landing, world.base):
        return None
    slug = record.task.slug
    return Refusal(
        "base",
        "the base moved after the checks ran: the approved change needs checks on its new base",
        f"lem land next {slug} names the steps to rebase and check it",
    )


def due(landing: Landing, world: World) -> Due | None:
    """A standing approval on a moved base resumes through its landing steps."""
    if landing.standing is None or not moved(landing, world.base):
        return None
    return Due(step="start", why="the approval stands: rebase and run the checks again")


def repair(landing: Landing) -> bool:
    """Whether a failed recheck keeps this approval out of the merge line."""
    refused = landing.refused
    return (
        landing.standing is not None
        and refused is not None
        and (refused.source, refused.kind, refused.by) == ("lem", "rule", "owner")
    )


def red(landing: Landing, run: Checked, end: CheckEnd) -> Refused | None:
    """Record that red checks prevented the approved merge, until the next proposal."""
    proposed = landing.proposed
    if landing.standing is None or proposed is None or run.outcome != "red":
        return None
    if proposed.base == run.base and not repair(landing):
        return None
    return Refused(
        tip=run.tip,
        source="lem",
        kind="rule",
        by="owner",
        line=end.say,
        at=end.at,
    )
