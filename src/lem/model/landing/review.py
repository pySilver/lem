"""`read`: the review before the pull request, by an agent that did not build the change
(`landing.md` C, row 5; D, review coverage).

The review holds while its newest answered attempt read this very tip, left no must-fix and was
of the floor's kind at the least. A record of another attempt or tip is refused; a third round,
a second silent attempt, a review's carry over a rebase or a commit of filed items, and the read
of a conflict's resolution are the step `land-review`'s, refused by name.
"""

from typing import TYPE_CHECKING, get_args

from lem.kernel.errors import Refusal
from lem.model.landing import review_said
from lem.model.landing.world import Due, Held, World, later
from lem.records.landing.record import Landing
from lem.records.landing.review import Reviewed

if TYPE_CHECKING:
    from lem.records.record import Record

STEP = "read"
KINDS: tuple[review_said.Kind, ...] = get_args(review_said.Kind.__value__)
# The rounds of a review the plain path takes; a third is the step `land-review`'s.
ROUNDS = 2


def floor(record: Record) -> review_said.Kind:
    """The least review the change gets: the full set for a careful request, a round after a
    review that found a must-fix, else one read."""
    shape = record.task.shape
    if shape is not None and shape.careful:
        return "full"
    reviews = (record.landing or Landing()).reviews
    return "round" if any(must_fix(review) for review in reviews) else "read"


def newest(landing: Landing) -> Reviewed | None:
    """The newest attempt that some reviewer answered."""
    answered = [review for review in landing.reviews if review.answered]
    return answered[-1] if answered else None


def must_fix(review: Reviewed) -> int:
    """How many must-fix the review found."""
    return sum(finding.level == "must-fix" for finding in review.findings)


def holds(record: Record, world: World) -> Held | Due:
    """Whether the newest answered review covers this tip and left no must-fix."""
    last = newest(record.landing or Landing())
    if last is None:
        return Due(step=STEP, why="no review read the change yet")
    if last.tip != world.tip:
        return Due(step=STEP, why="the tip changed after the last review")
    if must_fix(last):
        return Due(step=STEP, why=f"the last review left {must_fix(last)} must-fix")
    if KINDS.index(last.kind) < KINDS.index(floor(record)):
        return Due(
            step=STEP, why=f"the change gets the {floor(record)} set at the least"
        )
    return Held(why=f"review {last.attempt} read this tip and left no must-fix")


def limits(landing: Landing, said: review_said.Said) -> Refusal | None:
    """Why the attempt passes the plain path's bounds: a third round, or a second attempt
    nobody answered, is the step `land-review`'s."""
    answered = [review for review in landing.reviews if review.answered]
    if said.answered and len(answered) >= ROUNDS:
        return later("a third round of the review", "land-review")
    if not said.answered and len(landing.reviews) > len(answered):
        return later(
            "a second attempt of the review that nobody answered", "land-review"
        )
    return None


def refusal(record: Record, said: review_said.Said) -> Refusal | None:
    """Why the review as written down is not one this change may take."""
    slug, least = record.task.slug, floor(record)
    if KINDS.index(said.kind) < KINDS.index(least):
        return Refusal(
            "under-floor",
            f"this change gets the {least} set at the least, and the review was {said.kind}",
            f"run the {least} set, then lem land read {slug} --record FILE",
        )
    if said.answered and said.careful is None:
        return Refusal(
            "no-careful-call",
            "the review made no careful call: whether the change reaches what must never "
            "go wrong",
            f"the review says careful true or false, with why, in FILE for {slug}",
        )
    if said.careful and said.kind != "full":
        return Refusal(
            "careful-not-full",
            "the review calls the change careful, and a careful change gets the full set",
            f"run the project's full set, then lem land read {slug} --record FILE",
        )
    return None


def decide(record: Record, world: World, said: review_said.Said) -> Refusal | Reviewed:
    """The review attempt to record for the tip now, or why it is refused."""
    landing = record.landing or Landing()
    attempt = len(landing.reviews) + 1
    refused = (
        review_said.of_form(said, attempt, world)
        or limits(landing, said)
        or refusal(record, said)
    )
    if refused is not None:
        return refused
    outside = review_said.outside_of(said)
    return Reviewed(
        attempt=attempt,
        tip=said.tip,
        of="change",
        scope="whole",
        floor=floor(record),
        kind=said.kind,
        careful=said.careful,
        careful_why=said.careful_why,
        answered=said.answered,
        silent=said.silent,
        ran=said.ran,
        left_out=said.left_out,
        findings=review_said.counted(said) + outside,
        to_file=tuple(finding.id for finding in outside),
        at=world.now,
    )
