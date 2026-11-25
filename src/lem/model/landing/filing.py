"""`file`: every finding of the newest review gets its place (`landing.md` C, row 6; D,
filing).

The plain path places a finding under the bar, or a cheap one nobody fixed, as `seen`: a line of
the pull request with its reason. A finding over the bar becomes a backlog item in a commit of
its own, and `--same`, `--new` and `--again` judge an item that holds it already: those are the
step `land-review`'s.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing.review import newest
from lem.model.landing.world import Due, Held, World, later
from lem.records.landing.record import Landing
from lem.records.landing.review import Filed, Finding

if TYPE_CHECKING:
    from lem.records.record import Record

STEP = "file"


def unfiled(landing: Landing) -> tuple[Finding, ...]:
    """The findings of the newest review that wait for their place."""
    last = newest(landing)
    if last is None:
        return ()
    done = {filed.finding for filed in landing.filed}
    return tuple(
        finding
        for finding in last.findings
        if finding.id in last.to_file and finding.id not in done
    )


def holds(record: Record, world: World) -> Held | Due:
    """Whether every finding of the newest review has its place."""
    waiting = unfiled(record.landing or Landing())
    if waiting:
        return Due(step=STEP, why=f"{len(waiting)} findings wait for their place")
    return Held(why="every finding has its place")


def placed(finding: Finding) -> Refusal | Filed:
    """One finding's place: seen with its reason, or the refusal of an item."""
    if finding.against == "over":
        return later(
            f"the backlog item of {finding.id}, a finding over the bar", "land-review"
        )
    reason = finding.why or "no reason given"
    return Filed(
        finding=finding.id,
        disposition="seen",
        line=f"{finding.against}: {reason}",
    )


def decide(record: Record, world: World) -> Refusal | tuple[Filed, ...]:
    """The place of each finding that waits, or the refusal of the first that may not have
    one here."""
    places = [placed(finding) for finding in unfiled(record.landing or Landing())]
    refused = next((place for place in places if isinstance(place, Refusal)), None)
    if refused is not None:
        return refused
    return tuple(place for place in places if isinstance(place, Filed))
