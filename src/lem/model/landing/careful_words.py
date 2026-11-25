"""The careful calls that are judgments: the owner's word and the newest review's call
(`land.owner_says_careful` and `land.review_call` on `main`)."""

from typing import TYPE_CHECKING

from lem.records.decisions import Taken

if TYPE_CHECKING:
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record

# The owner's careful word, as the brief's line and the reason say it, and the question his
# decision answers (`stages/correct.md`, be-careful).
OWNER_SAYS = "the owner says so"
OWNER_ASKED = "whether the task is careful"


def owner_says(record: Record, *, owner: bool) -> tuple[str, ...]:
    """The owner's careful word: his decision `lem decisions log --by owner` keeps in the
    record (`stages/correct.md`, be-careful), or the brief's line `careful: the owner says
    so`, which `owner` gives (`land.owner_says_careful` on `main`)."""
    decided = any(
        isinstance(one, Taken)
        and one.by == "owner"
        and one.what == OWNER_ASKED
        and one.chose.startswith("careful")
        for one in record.task.decisions
    )
    return (OWNER_SAYS,) if decided or owner else ()


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
