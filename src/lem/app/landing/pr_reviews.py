"""The reviews in the pull request's checks (`main:land.pr_text`, `outside_words`,
`resolution_line`): each attempt with its kind, who answered and who did not, what it found in
the change, and what it saw outside the change: filed as items, fixed on the way, or seen."""

import re
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Filed, Finding, Reviewed

KIND_SAYS = MappingProxyType(
    {
        "read": "one read",
        "round": "a review round with the profiles that fit",
        "full": "the project's full set",
    }
)
LEVELS = ("must-fix", "should", "nit")


def named_by(number: str, text: str) -> bool:
    """Whether a text names a finding by its number (`r1.3`), and not another that starts
    the same (`r1.30`, `r11.3`)."""
    return re.search(rf"(?<![\w.]){re.escape(number)}(?![\w]|\.\d)", text) is not None


def outside(review: Reviewed) -> tuple[Finding, ...]:
    """The defects a review saw outside the change."""
    return tuple(found for found in review.findings if found.id in review.to_file)


def mended(found: Finding, filed: Filed | None, fixed: str) -> bool:
    """Whether a builder fixed a cheap defect on the way: filed so, or named by its number
    under the notes' `## Fixed on the way`."""
    named = found.against == "cheap" and named_by(found.id, fixed)
    return named or (filed is not None and filed.disposition == "cheap-fixed")


def words(review: Reviewed, landing: Landing, fixed: str) -> str:
    """What one review saw outside the change: how many, the items they were filed as, how
    many were fixed on the way, how many are seen and not filed; nothing for none."""
    defects = outside(review)
    if not defects:
        return ""
    filed = {found.finding: found for found in landing.filed}
    paths = [
        filed[found.id].path
        for found in defects
        if found.id in filed and filed[found.id].path
    ]
    fixes = sum(1 for found in defects if mended(found, filed.get(found.id), fixed))
    seen = len(defects) - len(paths) - fixes
    plural = "" if len(defects) == 1 else "s"
    said = f"; it saw {len(defects)} defect{plural} outside the change"
    if paths:
        said += ", filed as " + ", ".join(f"`{path}`" for path in paths)
    if fixes:
        said += f"; {fixes} fixed on the way"
    return said + (f"; {seen} seen, not filed" if seen else "")


def found(review: Reviewed) -> str:
    """What a review found in the change: its call and the count of each level."""
    if not review.answered:
        return "not reviewed"
    change = [found for found in review.findings if found.id not in review.to_file]
    counts = {level: sum(1 for one in change if one.level == level) for level in LEVELS}
    call = "must-fix" if counts["must-fix"] else "clean"
    listed = ", ".join(f"{count} {level}" for level, count in counts.items())
    return f"{call}, {listed}"


def review_line(review: Reviewed, landing: Landing, fixed: str, *, full: bool) -> Lines:
    """One review: its kind, who answered and who did not, what it found, what it saw
    outside the change, and on the standard track why each profile ran or was left out."""
    names = ", ".join(review.answered)
    who = f"answered: {names}" if review.answered else "no source answered"
    kind = KIND_SAYS[review.kind]
    if review.of == "resolution":
        return (
            f"- the read of the conflict's resolution ({kind}; {who}): {found(review)}",
        )
    quiet = "".join(f"; no answer from {one.name} ({one.why})" for one in review.silent)
    said = found(review) + words(review, landing, fixed)
    line = f"- the review, round {review.attempt} ({kind}; {who}{quiet if full else ''}): {said}"
    if not full:
        return (line,)
    ran = tuple(f"  - ran {one.name}: {one.why}" for one in review.ran)
    left = tuple(f"  - left out {one.name}: {one.why}" for one in review.left_out)
    return (line, *ran, *left)


def lines(landing: Landing, fixed: str, *, full: bool) -> Lines:
    """Each review attempt, in its order."""
    return tuple(
        line
        for review in landing.reviews
        for line in review_line(review, landing, fixed, full=full)
    )
