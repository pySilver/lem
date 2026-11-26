"""A review round as the board says it (`board_model.review_line` on `main`): which round, its
kind, its verdict, and its counts of findings by level."""

from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.landing.review import Reviewed

# The three kinds of review, in the words of the landing.
KIND = MappingProxyType(
    {
        "read": "one read",
        "round": "a round with the profiles that fit",
        "full": "the project's full set",
    }
)
MUST_FIX = "must-fix"


def counts(review: Reviewed) -> tuple[int, int, int]:
    """The review's findings: must-fix, should, nit."""
    found = review.counts
    return found.must_fix, found.should, found.nit + found.outside


def verdict(review: Reviewed) -> str:
    """The result of an answered review, or that nobody reviewed it."""
    if not review.answered:
        return "not reviewed"
    return MUST_FIX if counts(review)[0] else "clean"


def head(review: Reviewed) -> str:
    """`round 2`, or the conflict's resolution."""
    if review.of == "resolution":
        return "the conflict’s resolution"
    return f"round {review.attempt}"


def line(review: Reviewed) -> str:
    """`round 1, a round with the profiles that fit: must-fix, 1 must-fix, 1 should, 0
    nit`."""
    must, should, nit = counts(review)
    kind = KIND[review.kind]
    said = f"{verdict(review)}, {must} must-fix, {should} should, {nit} nit"
    return f"{head(review)}, {kind}: {said}"
