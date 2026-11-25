"""`read`: the review before the pull request, by an agent that did not build the change
(`landing.md` C, row 5; D, review coverage).

The review holds while its newest answered attempt read this very tip, left no must-fix and was
of the floor's kind at the least. A review's carry over a rebase or a commit of filed items, two
rounds, two silent attempts and the read of a conflict's resolution are the step
`land-review`'s.
"""

from typing import TYPE_CHECKING, Literal, get_args

from lem.kernel.errors import Refusal
from lem.model.landing.world import Due, Held, World
from lem.records.base import Frozen
from lem.records.landing.record import Landing
from lem.records.landing.review import Finding, Named, Reviewed

if TYPE_CHECKING:
    from lem.records.record import Record

STEP = "read"
type Kind = Literal["read", "round", "full"]
KINDS: tuple[Kind, ...] = get_args(Kind.__value__)


class Said(Frozen, frozen=True, kw_only=True):
    """What the review agent wrote down: its kind, who answered and who was silent, the
    careful call and why, and its findings (`lem land read --record FILE`)."""

    kind: Kind
    answered: tuple[str, ...] = ()
    silent: tuple[Named, ...] = ()
    careful: bool | None = None
    careful_why: str | None = None
    findings: tuple[Finding, ...] = ()


def floor(record: Record) -> Kind:
    """The least review the change gets: the full set for a careful request, else one read."""
    shape = record.task.shape
    return "full" if shape is not None and shape.careful else "read"


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


def refusal(record: Record, said: Said) -> Refusal | None:
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


def decide(record: Record, world: World, said: Said) -> Refusal | Reviewed:
    """The review attempt to record for the tip now, or why it is refused."""
    refused = refusal(record, said)
    if refused is not None:
        return refused
    landing = record.landing or Landing()
    return Reviewed(
        attempt=len(landing.reviews) + 1,
        tip=world.tip or "",
        of="change",
        scope="whole",
        floor=floor(record),
        kind=said.kind,
        careful=said.careful,
        careful_why=said.careful_why,
        answered=said.answered,
        silent=said.silent,
        findings=said.findings,
        to_file=tuple(finding.id for finding in said.findings),
        at=world.now,
    )
