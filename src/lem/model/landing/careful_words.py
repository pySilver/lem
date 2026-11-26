"""The careful calls that are judgments: the owner's word and the newest review's call
(`land.owner_says_careful` and `land.review_call` on `main`)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record


def owner_says(record: Record) -> tuple[str, ...]:
    """The owner's careful word as `/lem be-careful` records it."""
    return ("the owner says so",) if record.task.owner_careful else ()


def after_proposal(record: Record) -> bool:
    """The owner's careful word needs a new landing for a proposal made without it."""
    landing = record.landing
    if landing is None or landing.proposed is None:
        return False
    return record.task.owner_careful is not None and not landing.proposed.careful


def standing(landing: Landing) -> list[Reviewed]:
    """The answered reviews whose careful call stands: the newest round of the change and
    each read of a resolution after it."""
    answered = [review for review in landing.reviews if review.answered]
    rounds = [at for at, review in enumerate(answered) if review.of == "change"]
    first = rounds[-1] if rounds else len(answered) - 1
    return answered[max(first, 0) :]


def review_reason(landing: Landing) -> tuple[str, ...]:
    """The careful call of the standing reviews: a read of a resolution that calls the change
    not careful takes back no call of the round (prompt step 1, `land.moved_carry` on
    `main`)."""
    called = [review.careful_why for review in standing(landing) if review.careful]
    return (f"the review says so: {called[0]}",) if called else ()
