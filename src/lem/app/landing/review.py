"""`lem land read`: what review is due, or the record of the review an agent ran.

With no file the step says what the review is: its attempt, its floor, the tip and the careful
topics. With `--record FILE` it takes the agent's JSON, in the form `prompts/review.md` gives
(`model.landing.review_said.Said`), for the attempt and the tip now. Jev's word and the seams of
an unread review are the step `land-review`'s.
"""

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import changes, frame, step
from lem.kernel.errors import Refusal
from lem.model.landing import review, review_said
from lem.records.base import Frozen, Sha
from lem.records.journal.landing import ReviewRound

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record


class ReadDue(Frozen, frozen=True, kw_only=True):
    """The review that is due: its attempt, its floor, the tip it reads, and the careful
    topics of the shape."""

    attempt: int
    floor: review_said.Kind
    tip: Sha
    careful: tuple[str, ...] = ()


def said(path: str) -> review_said.Said:
    """The review agent's file; a file that is not its JSON is refused with the fix."""
    try:
        return msgspec.json.decode(Path(path).read_bytes(), type=review_said.Said)
    except (OSError, msgspec.DecodeError) as error:
        raise Refusal(
            "review-file",
            f"{path} is not the review's record: {error}",
            "write the record as prompts/review.md says: attempt, tip, kind, ran, left_out, "
            "answered, silent, must_fix, should, nit, outside, careful, careful_why",
        ) from error


def reviewed(record: Record, *, attempt: Reviewed) -> Record:
    """The record with the review attempt, and its round in the journal."""
    before = record.landing.reviews if record.landing else ()
    changed = changes.landing(record, reviews=(*before, attempt))
    return changes.noted(changed, ReviewRound(at=attempt.at, review=attempt))


def act(context: frame.Context, *, path: str | None) -> ReadDue | Reviewed:
    """Say what is due, or record the review of the file at `path`."""
    record, world = context.record, context.world
    if path is None:
        shape = record.task.shape
        before = record.landing.reviews if record.landing else ()
        return ReadDue(
            attempt=len(before) + 1,
            floor=review.floor(record),
            tip=world.tip or "",
            careful=shape.careful if shape else (),
        )
    attempt = review.decide(record, world, said(path))
    if isinstance(attempt, Refusal):
        raise attempt
    context.write(record, partial(reviewed, attempt=attempt))
    return attempt


def run(folder: Path, slug: str, path: str | None) -> Envelope:
    """`lem land read SLUG [--record FILE]`."""
    return step.landed(folder, slug, "read", partial(act, path=path))
