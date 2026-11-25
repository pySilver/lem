"""`file`: every defect a review saw outside the change gets its place (`landing.md` C, row 6;
D, filing; `land.cmd_file` on `main`).

It holds while each defect of the reviews that answered has its place. `decide` gives each
waiting defect its place (`model/landing/filing_place.py`) and the items to write, one commit
for each review round; `--same` and `--new` judge an item Jev named, and `--again` writes once
more an item `file` filed that the tip no longer holds.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import filing_asks, filing_flags, filing_place, filing_plan
from lem.model.landing.world import Due, Held, World
from lem.records.base import Frozen
from lem.records.landing.record import Landing
from lem.records.landing.review import Filed, Finding

if TYPE_CHECKING:
    from lem.records.record import Record

STEP = "file"


class Placed(Frozen, frozen=True, kw_only=True):
    """Each waiting defect's place, the items to write, and the defects Jev is asked about
    before anything is written: those that get a file of their own with no word of the
    owner's agent on them."""

    filed: tuple[Filed, ...] = ()
    writes: tuple[filing_place.Write, ...] = ()
    asks: tuple[Finding, ...] = ()

    @classmethod
    def made(
        cls, left: filing_plan.Waiting, places: list[filing_plan.Place], named: set[str]
    ) -> Placed:
        """The places of the waiting defects `left`; `named` are those `--same` and `--new`
        judged."""
        return cls(
            filed=tuple(filed for filed, _ in places),
            writes=tuple(write for _, write in places if write is not None),
            asks=filing_asks.asks_of(left, places, named),
        )


def waiting(landing: Landing, again: tuple[str, ...] = ()) -> filing_plan.Waiting:
    """Each defect of an answered review that waits for its place, with its review: one with
    no place yet, and each whose item `again` names."""
    done = {filed.finding for filed in landing.filed if filed.path not in again}
    return tuple(
        (review, finding)
        for review in landing.reviews
        if review.answered
        for finding in review.findings
        if finding.id in review.to_file and finding.id not in done
    )


def holds(record: Record, world: World) -> Held | Due:
    """Whether every defect of the reviews that answered has its place."""
    left = waiting(record.landing or Landing())
    if left:
        return Due(
            step=STEP,
            why=f"{len(left)} defects outside the change wait for their place",
        )
    return Held(why="every defect outside the change has its place")


def refused(
    landing: Landing, shelf: filing_place.Shelf, flags: filing_flags.Flags, slug: str
) -> Refusal | dict[str, str]:
    """The defects `--same` names with their items, or why the words may not be taken."""
    same = filing_flags.same_of(flags, shelf.folder, shelf.paths)
    if isinstance(same, Refusal):
        return same
    gone = filing_asks.gone_of(landing, shelf)
    again = filing_asks.again_of(landing, shelf, again=flags.again)
    free = filing_asks.free_of(waiting(landing, again), shelf)
    found = (
        filing_flags.both_refused(same, flags)
        or filing_flags.stray_refused({*same, *flags.new}, free)
        or filing_flags.gone_refused(gone, slug, again=flags.again)
    )
    return found or same


def decide(
    record: Record, world: World, shelf: filing_place.Shelf, flags: filing_flags.Flags
) -> Refusal | Placed:
    """Each waiting defect's place, or why none may be given now."""
    landing, slug = record.landing or Landing(), record.task.slug
    same = refused(landing, shelf, flags, slug)
    if isinstance(same, Refusal):
        return same
    left = waiting(landing, filing_asks.again_of(landing, shelf, again=flags.again))
    places = filing_plan.places_of(record, world, left, shelf, same)
    return Placed.made(left, places, {*same, *flags.new})
