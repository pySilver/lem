"""What one review saw outside the change, in its line of the pull request's checks
(`main:land.outside_words`): how many defects, the items they were filed as, how many a builder
fixed on the way (a cheap defect the notes' `## Fixed on the way` names by its number), and how
many are seen and not filed."""

import re
from functools import partial
from typing import TYPE_CHECKING

from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Filed, Finding, Reviewed

type Places = dict[str, Filed]


def named_by(number: str, text: str) -> bool:
    """Whether a text names a finding by its number (`r1.3`), and not another that starts
    the same (`r1.30`, `r11.3`)."""
    return re.search(rf"(?<![\w.]){re.escape(number)}(?![\w]|\.\d)", text) is not None


def outside(review: Reviewed) -> tuple[Finding, ...]:
    """The defects a review saw outside the change."""
    return tuple(found for found in review.findings if found.id in review.to_file)


def mended(fixed: str, places: Places, found: Finding) -> bool:
    """Whether a builder fixed a cheap defect on the way: filed so, or named by its number
    under the notes' `## Fixed on the way`."""
    place = places.get(found.id)
    if place is not None and place.disposition == "cheap-fixed":
        return True
    return found.against == "cheap" and named_by(found.id, fixed)


def path_of(places: Places, found: Finding) -> str | None:
    """The item a defect was filed as, or None."""
    place = places.get(found.id)
    return place.path if place else None


class Tally(Frozen, frozen=True, kw_only=True):
    """What one review saw outside the change: the defects, the items they were filed as,
    and how many were fixed on the way."""

    count: int
    paths: tuple[str, ...]
    fixes: int

    def said(self) -> str:
        """The words of the review's line; nothing for a review that saw none."""
        if not self.count:
            return ""
        seen = self.count - len(self.paths) - self.fixes
        noun = "defect" if self.count == 1 else "defects"
        filed = filed_as(self.paths)
        fixed = f"; {self.fixes} fixed on the way" if self.fixes else ""
        unfiled = f"; {seen} seen, not filed" if seen else ""
        return f"; it saw {self.count} {noun} outside the change{filed}{fixed}{unfiled}"


def filed_as(paths: tuple[str, ...]) -> str:
    """The part of a review's words that names the items its defects were filed as."""
    listed = ", ".join(f"`{path}`" for path in paths)
    return f", filed as {listed}" if paths else ""


def words(review: Reviewed, landing: Landing, fixed: str) -> str:
    """What one review saw outside the change, in the words of its line."""
    defects = outside(review)
    places = {found.finding: found for found in landing.filed}
    paths = tuple(filter(None, map(partial(path_of, places), defects)))
    fixes = sum(map(partial(mended, fixed, places), defects))
    return Tally(count=len(defects), paths=paths, fixes=fixes).said()
