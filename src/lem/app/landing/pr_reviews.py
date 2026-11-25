"""The reviews in the pull request's checks (`main:land.pr_text`, `resolution_line`): each
attempt with its kind, who answered and who did not, what it found in the change and what it
saw outside it, and on the standard track why each profile ran or was left out."""

from collections import Counter
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.landing.pr_words import words

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Reviewed

KIND_SAYS = MappingProxyType(
    {
        "read": "one read",
        "round": "a review round with the profiles that fit",
        "full": "the project's full set",
    }
)
LEVELS = ("must-fix", "should", "nit")
QUIET = "; no answer from {0.name} ({0.why})"
RAN = "  - ran {0.name}: {0.why}"
LEFT = "  - left out {0.name}: {0.why}"


def levels_of(review: Reviewed) -> Counter[str]:
    """How many findings of each level a review found in the change."""
    change = (one for one in review.findings if one.id not in review.to_file)
    return Counter(one.level for one in change)


def found(review: Reviewed) -> str:
    """What a review found in the change: its call and the count of each level."""
    if not review.answered:
        return "not reviewed"
    counts = levels_of(review)
    call = "must-fix" if counts["must-fix"] else "clean"
    return f"{call}, {counted(counts)}"


def counted(counts: Counter[str]) -> str:
    """Each level with its count, in the order of `LEVELS`."""
    pairs = ((counts[level], level) for level in LEVELS)
    return ", ".join(f"{count} {level}" for count, level in pairs)


def who(review: Reviewed, *, full: bool) -> str:
    """Who answered, and on the standard track who did not and why."""
    names = ", ".join(review.answered)
    said = f"answered: {names}" if review.answered else "no source answered"
    if not full:
        return said
    return said + "".join(map(QUIET.format, review.silent))


def profiles(review: Reviewed) -> Lines:
    """Why each profile of a round ran or was left out."""
    ran = tuple(map(RAN.format, review.ran))
    return ran + tuple(map(LEFT.format, review.left_out))


def review_line(review: Reviewed, landing: Landing, fixed: str, *, full: bool) -> Lines:
    """One review attempt, or the read of a conflict's resolution."""
    kind, answered = KIND_SAYS[review.kind], who(review, full=full)
    if review.of == "resolution":
        said = found(review)
        return (
            f"- the read of the conflict's resolution ({kind}; {answered}): {said}",
        )
    said = found(review) + words(review, landing, fixed)
    line = f"- the review, round {review.attempt} ({kind}; {answered}): {said}"
    return (line, *profiles(review)) if full else (line,)


def lines(landing: Landing, fixed: str, *, full: bool) -> Lines:
    """Each review attempt, in its order."""
    return tuple(
        line
        for review in landing.reviews
        for line in review_line(review, landing, fixed, full=full)
    )
