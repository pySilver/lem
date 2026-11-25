"""`read`: the review before the pull request, by an agent that did not build the change
(`landing.md` C, row 5; D, review coverage).

The review holds while the newest answered attempt covers the tip, left no must-fix, and was of
its floor at the least; or once two rounds were used, or two attempts in a row were silent:
then the request goes on to the owner, not green. It covers the tip it read, and the commits
`file` made after it, which only add the backlog items of its defects (`Checked.items_after`).
The carry over a clean rebase is `model/landing/carry.py`'s, which the step `land-base` builds.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.model.landing import (
    careful,
    review_cover,
    review_due,
    review_form,
    review_outside,
    review_said,
)
from lem.model.landing.world import Due, Held, World
from lem.records.landing.record import Landing
from lem.records.landing.review import Reviewed

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.records.record import Record

STEP = "read"
RESOLVED = "a builder resolved a conflict with the base: one read of what it changed"


def newest(landing: Landing) -> Reviewed | None:
    """The newest attempt, when some reviewer answered it. None while the newest attempt is
    one nobody answered: a review was due after the last answered one, so that one clears
    nothing, and the request goes on as not reviewed (`land.due_of` on `main`)."""
    found = landing.reviews[-1] if landing.reviews else None
    return found if found is not None and found.answered else None


def must_fix(review: Reviewed) -> int:
    """How many must-fix the review found."""
    return sum(finding.level == "must-fix" for finding in review.findings)


def unmet(record: Record, review: Reviewed | None, world: World) -> tuple[str, ...]:
    """What the newest answered review leaves open for the change as it is now."""
    if review is None:
        return ("no review read the change yet",)
    landing = record.landing or Landing()
    least = review_due.floor(
        record, careful.reasons(record, careful.Edits()), resolution=False
    )
    left = (
        f"the last one left {must_fix(review)} must-fix" if must_fix(review) else None,
        None
        if review_cover.covers(review, landing, world)
        else "nobody reviewed what changed after it",
        review_cover.too_small(review, landing, least),
    )
    return tuple(reason for reason in left if reason)


def holds(record: Record, world: World) -> Held | Due:
    """Whether a review covers the change as it is now, or the request goes on without one."""
    landing = record.landing or Landing()
    if review_due.resolution_due(landing, world) is not None:
        return review_cover.resolution_held(landing) or Due(step=STEP, why=RESOLVED)
    left = unmet(record, newest(landing), world)
    if not left:
        return Held(why="the newest review covers this change, with no must-fix")
    gone = review_cover.gone_on(landing, left)
    return gone or Due(step=STEP, why=left[0])


def floor_of(record: Record, world: World, facts: review_due.Facts) -> review_due.Floor:
    """The floor of the review that is due, a conflict's resolution or the change."""
    landing = record.landing or Landing()
    resolution = review_due.resolution_due(landing, world) is not None
    return review_due.floor(record, facts.careful, resolution=resolution)


def refused(
    record: Record, world: World, said: review_said.Said, facts: review_due.Facts
) -> Refusal | None:
    """Why the review as written down is not one this change may take."""
    slug = record.task.slug
    least = floor_of(record, world, facts)
    recorded = tuple(review.attempt for review in (record.landing or Landing()).reviews)
    checks = (
        partial(review_form.attempt_refused, said, len(recorded) + 1, recorded),
        partial(review_form.tip_refused, said.tip, world.tip or "", slug),
        partial(review_form.under_floor, said, least, slug),
        partial(review_form.call_refused, said, slug),
        partial(review_form.names_refused, said),
        partial(review_outside.refused, said, facts.folder, facts.at_base),
        partial(review_form.bar_refused, said, facts.lowered),
    )
    found = (check() for check in checks)
    return next((refusal for refusal in found if refusal), None)


def decide(
    record: Record, world: World, said: review_said.Said, facts: review_due.Facts
) -> Refusal | Reviewed:
    """The review attempt to record for the tip now, or why it is refused."""
    found = refused(record, world, said, facts)
    if found is not None:
        return found
    landing = record.landing or Landing()
    resolution = review_due.resolution_due(landing, world) is not None
    outside = review_outside.findings(said)
    last = newest(landing)
    return Reviewed(
        attempt=said.attempt,
        tip=said.tip,
        of="resolution" if resolution else "change",
        scope="resolution" if resolution and last and not must_fix(last) else "whole",
        floor=floor_of(record, world, facts).kind,
        kind=said.kind,
        careful=said.careful,
        careful_why=said.careful_why,
        answered=said.answered,
        silent=review_said.kept(said.silent),
        ran=review_said.kept(said.ran),
        left_out=review_said.kept(said.left_out),
        findings=review_said.counted(said) + outside,
        to_file=tuple(finding.id for finding in outside),
        at=world.now,
    )
