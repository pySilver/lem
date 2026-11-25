"""What was seen outside the change, in the pull request's text (`main:land.outside_parts`,
`item_lines`, `seen_line`): each item the branch adds to the backlog, or a review's finding was
filed as, under the heading its `worth` at the tip gives, and a line for each defect a review saw
that has no item and that no builder fixed on the way."""

from typing import TYPE_CHECKING

from lem.app.landing.pr_words import mended, outside
from lem.model.landing.propose_facts import Filing
from lem.model.landing.propose_lines import FILED, NOT_WORTH
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.app.landing.pr_inputs import Lines
    from lem.model.landing.propose_facts import Facts
    from lem.records.landing.review import Finding
    from lem.records.record import Record

type Headed = dict[str, list[str]]


def reviewed(landing: Landing, paths: set[str]) -> list[Filing]:
    """Each item a review's finding was filed as that is not among `paths` (an item of the
    base that holds the same defect), with the finding's title and the item's worth."""
    titles = {
        one.id: one.title for review in landing.reviews for one in review.findings
    }
    found = []
    for filed in landing.filed:
        if filed.path and filed.path not in paths:
            paths.add(filed.path)
            title = titles.get(filed.finding)
            found.append(Filing(path=filed.path, title=title, worth=filed.worth))
    return found


def filing_line(filing: Filing) -> str:
    """An item's line: `- `PATH`: TITLE`."""
    said = f": {filing.title}" if filing.title else ""
    return f"- `{filing.path}`{said}"


def headed(landing: Landing, facts: Facts) -> Headed:
    """The line of each item under the heading its `worth` gives: the items the branch
    adds, then the review's that the branch does not."""
    added = list(facts.added)
    every = added + reviewed(landing, {one.path for one in added})
    by: Headed = {FILED: [], NOT_WORTH: []}
    for filing in every:
        worth = (filing.worth or "").strip().lower()
        by[NOT_WORTH if worth == "no" else FILED].append(filing_line(filing))
    return by


def seen_line(found: Finding) -> str:
    """A defect seen and not filed: its place, its title, the review's call with why, and
    the open item that holds it."""
    line = f"- `{found.where}`: {found.title}"
    if found.why:
        line = f"{line}; {found.against}: {found.why}"
    if found.open:
        line = f"{line}; an open item holds it, `{found.open}`"
    return line


def seen(landing: Landing, fixed: str) -> Lines:
    """Each defect a review saw that has no item and that a builder did not fix on the
    way."""
    places = {found.finding: found for found in landing.filed}
    filed = {found.finding for found in landing.filed if found.path}
    left = (found for found in defects_of(landing) if found.id not in filed)
    kept = (found for found in left if not mended(fixed, places, found))
    return tuple(map(seen_line, kept))


def defects_of(landing: Landing) -> Iterator[Finding]:
    """Each defect outside the change of each review that someone answered."""
    for review in landing.reviews:
        if review.answered:
            yield from outside(review)


def parts(record: Record, facts: Facts, fixed: str) -> tuple[Headed, Lines]:
    """The step's item lines by heading, and its seen lines."""
    landing = record.landing or Landing()
    return headed(landing, facts), seen(landing, fixed)
