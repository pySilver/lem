"""What a retro decided about a group, written beside the queue, and the lessons earlier retros
recorded (`corrections.cmd_record` and `cmd_lessons` on `main`).

A lesson needs its sentence and its file: a lesson in no file is read by no later session, and
the list then counts it as kept (two such rows were recorded before this refusal,
corrections-reviews.jsonl of mybaze, 2026-11-20 and 2026-11-21 UTC). A lesson that went into a
proposal of the retro is recorded `proposed`, with the file the proposal would change and the
proposal's name in its sentence.
"""

from typing import TYPE_CHECKING, Literal

from lem.addons.corrections import groups, queue
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.records.corrections import CorrectionReview

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment

type Decision = Literal["lesson", "not_lesson"]
type Verdict = Literal[
    "accepted", "changed", "rejected", "proposed", "missed", "unasked"
]


class Review(Frozen, frozen=True, kw_only=True):
    """What the retro decided about one group: a lesson or not, the verdict, the file the
    lesson went to, and its sentence."""

    gid: str
    decision: Decision
    verdict: Verdict
    target: str | None = None
    lesson: str | None = None


class Recorded(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The record written: the group, its entries, the decision and the verdict."""

    group: str
    entries: int
    decision: Decision
    verdict: Verdict


def recorded(state: Path, review: Review, now: Moment) -> Recorded:
    """Write the review of each entry of the group; refused for a lesson with no sentence or
    no file, and for a group that is not unreviewed."""
    if review.decision == "lesson":
        lesson_checked(review)
    entries = groups.group_of(state, review.gid)
    for entry in entries:
        line = CorrectionReview(
            at=entry.at,
            session=entry.session,
            group=review.gid,
            p_lesson=entry.p_lesson,
            reviewed=now,
            decision=review.decision,
            verdict=review.verdict,
            target=review.target,
            lesson=review.lesson,
        )
        queue.appended(state / queue.REVIEWS, line)
    return Recorded(
        group=review.gid,
        entries=len(entries),
        decision=review.decision,
        verdict=review.verdict,
    )


def lesson_checked(review: Review) -> None:
    """Refuse a lesson with no sentence or no file."""
    if not (review.lesson or "").strip():
        raise Refusal(
            "lesson-words",
            "a lesson needs --lesson: the sentence an agent could follow next time",
            "give --lesson",
        )
    if not (review.target or "").strip():
        raise Refusal(
            "lesson-target",
            "a lesson needs --target: the file the lesson went to, the one that already "
            "holds it, or the file its proposal would change",
            "give --target",
        )
