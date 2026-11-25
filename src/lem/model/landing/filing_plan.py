"""The place of each defect `file` gives (`land.cmd_file` on `main`): the round of its review,
where it was seen, and its place by the review's call and the open item that holds it."""

from typing import TYPE_CHECKING

import msgspec

from lem.model.landing import filing_place, items
from lem.records.landing.record import Landing
from lem.records.landing.review import Filed

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.review import Finding, Reviewed
    from lem.records.record import Record

type Waiting = tuple[tuple[Reviewed, Finding], ...]
type Place = tuple[Filed, filing_place.Write | None]


def round_of(landing: Landing, review: Reviewed) -> int:
    """The round of the review: the answered reviews of the change up to it."""
    upto = landing.reviews[: landing.reviews.index(review) + 1]
    rounds = [one for one in upto if one.answered and one.of == "change"]
    return max(len(rounds), 1)


def seen_of(review: Reviewed, record: Record, world: World) -> filing_place.Seen:
    """Where the review's defects were seen, and the day they are filed."""
    return filing_place.Seen(
        round=round_of(record.landing or Landing(), review),
        slug=record.task.slug,
        day=review.at.date().isoformat(),
        today=world.now.date().isoformat(),
    )


def place(
    finding: Finding,
    shelf: filing_place.Shelf,
    same: dict[str, str],
    seen: filing_place.Seen,
) -> Place:
    """One defect's place: a line for a cheap one; the open item that holds it (`--same`
    names it, else the review's `open`); or an item, beside the open one when that says
    `worth: no` and the defect is over the bar."""
    held = same.get(finding.id) or finding.open
    if finding.against == "cheap":
        line = filing_place.seen_line(finding)
        return Filed(finding=finding.id, disposition="seen", line=line), None
    if held is None or held not in shelf.paths:
        return filing_place.itemized(finding, shelf, seen, None)
    refuted = {found.path for found in shelf.shelved if found.worth == "no"}
    if finding.against == "over" and held in refuted:
        return filing_place.itemized(finding, shelf, seen, held)
    line = filing_place.seen_line(finding, held)
    return Filed(finding=finding.id, disposition="same", path=held, line=line), None


def places_of(
    record: Record,
    world: World,
    left: Waiting,
    shelf: filing_place.Shelf,
    same: dict[str, str],
) -> list[Place]:
    """The place of each waiting defect; `same` names the item that holds a defect."""
    found: list[Place] = []
    for review, finding in left:
        made = place(finding, shelf, same, seen_of(review, record, world))
        found.append(made)
        shelf = shelved(shelf, made[1])
    return found


def shelved(
    shelf: filing_place.Shelf, write: filing_place.Write | None
) -> filing_place.Shelf:
    """The shelf with an item this run writes, so that the next defect's item takes another
    name, or finds it when it is the same defect."""
    if write is None:
        return shelf
    found = items.read(write.path, write.text)
    more = (*shelf.shelved, found) if found else shelf.shelved
    paths = shelf.paths | {write.path}
    return msgspec.structs.replace(shelf, paths=paths, shelved=more)
