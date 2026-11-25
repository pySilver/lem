"""The careful calls that are judgments: the owner's word and the newest review's call
(`land.owner_says_careful` and `land.review_call` on `main`)."""

from typing import TYPE_CHECKING

from lem.records.decisions import Taken

if TYPE_CHECKING:
    from lem.records.landing.record import Landing
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


def review_reason(landing: Landing) -> tuple[str, ...]:
    """The careful call of the newest review that answered, when it says careful."""
    answered = [review for review in landing.reviews if review.answered]
    call = answered[-1] if answered else None
    if call is None or not call.careful:
        return ()
    why = call.careful_why
    return (f"the review says so: {why}",)
