"""Which review a change gets (`land.due_of` on `main`): its floor, the rounds and the silent
attempts so far, and the read of a builder's resolution of a conflict.

The floor is what no judgment goes under: the full set for a careful request, a round for a
large plan or after a review that found a must-fix, else one read. Which profiles fit a change
is read from the diff and from what each profile is for, by an agent: no code decides that.
"""

from typing import TYPE_CHECKING, Literal

from lem.model.landing.review_said import Kind
from lem.records.base import Frozen
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.review import Reviewed
    from lem.records.landing.start import Resolution
    from lem.records.record import Record

# A plan of more tasks than this is large: it gets a round at the least. The three-touches
# plan's own line (2026-11-15), not a measurement.
LARGE_AFTER = 3
# The rounds of review a change gets; what the last of them leaves open goes to the owner
# (`stages/land.md`, step 5).
ROUNDS = 2
# A review that no source answered is started once more; after this many in a row the request
# goes on to the owner as not reviewed (`stages/land.md`, step 5).
SILENT_REVIEWS = 2


class Floor(Frozen, frozen=True, kw_only=True):
    """The least review the change gets, and why."""

    kind: Kind
    why: str


class Facts(Frozen, frozen=True, kw_only=True):
    """What `read --record` reads besides the record and the world: each reason the request
    is careful, the backlog folder, its files at the base, and the files whose bar the
    change lowers."""

    careful: tuple[str, ...] = ()
    folder: str = "docs/backlog"
    at_base: frozenset[str] = frozenset()
    lowered: tuple[str, ...] = ()


def rounds(landing: Landing) -> tuple[Reviewed, ...]:
    """The answered reviews of the change; the read of a resolution is no round."""
    return tuple(
        review
        for review in landing.reviews
        if review.answered and review.of == "change"
    )


def silent_run(landing: Landing) -> int:
    """How many attempts in a row, the newest last, no source answered."""
    count = 0
    for review in reversed(landing.reviews):
        if review.answered:
            break
        count += 1
    return count


def resolution_due(landing: Landing, world: World) -> Resolution | None:
    """A builder's resolution of a conflict whose one read is due: made on this very tip,
    not read yet, after the newest answered review read the tip before the rebase and left no
    must-fix (`land.cmd_base` and `land.due_of` on `main`). A commit after it, or a must-fix
    the review left, makes the change one the rules of a change review whole."""
    found = landing.resolution
    if found is None or found.read is not None or found.after != world.tip:
        return None
    answered = [review for review in landing.reviews if review.answered]
    if not answered or answered[-1].tip != found.before:
        return None
    if answered[-1].counts.must_fix:
        return None
    return found


def floor(
    record: Record, careful: tuple[str, ...], *, resolution: bool = False
) -> Floor:
    """The least review the change gets now, and why."""
    if resolution:
        kind: Literal["read", "full"] = "full" if careful else "read"
        return Floor(kind=kind, why="a builder resolved a conflict with the base")
    if careful:
        return Floor(kind="full", why=f"the request is careful: {careful[0]}")
    plan = record.task.plan
    tasks = None if plan is None else plan.tasks
    if tasks is not None and tasks > LARGE_AFTER:
        return Floor(kind="round", why=f"the plan has {tasks} tasks, more than three")
    landing = record.landing or Landing()
    answered = (review for review in landing.reviews if review.answered)
    if any(review.counts.must_fix for review in answered):
        return Floor(
            kind="round",
            why="an earlier review found a must-fix: after its fix a round reviews the change",
        )
    return Floor(
        kind="read",
        why="nothing asks for more than one read: the diff and what each profile is for decide",
    )
