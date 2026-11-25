"""What was seen outside the change, in the pull request's text (`main:land.outside_parts`,
`item_lines`, `seen_line`, `placed`): each item the branch adds to the backlog under the
heading its `worth` at the tip gives, and a line for each defect a review saw that has no item
and that no line under the notes' `## Fixed on the way` names by its number.

A notes line that names an item takes the place of the step's line of it, so no item is written
twice and none under the other heading.
"""

import re
from typing import TYPE_CHECKING

from lem.app.landing import pr_reviews
from lem.app.landing.pr_inputs import Lines
from lem.model.landing.propose_lines import FILED, NOT_WORTH
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts
    from lem.records.landing.review import Finding
    from lem.records.record import Record

type Heading = str


def entries(landing: Landing, facts: Facts) -> list[tuple[str, str | None, str | None]]:
    """Each item the branch adds, with its title and `worth` at the tip, then each item a
    review's finding was filed as that the branch does not add (one of the base holds it)."""
    found = [(item.path, item.title, item.worth) for item in facts.added]
    paths = {path for path, _, _ in found}
    findings = {one.id: one for review in landing.reviews for one in review.findings}
    for filed in landing.filed:
        defect = findings.get(filed.finding)
        if filed.path and filed.path not in paths:
            paths.add(filed.path)
            found.append((filed.path, defect.title if defect else None, filed.worth))
    return found


def items(landing: Landing, facts: Facts) -> dict[Heading, list[str]]:
    """The line of each item, `- `PATH`: TITLE`, under the heading its `worth` gives."""
    by: dict[Heading, list[str]] = {FILED: [], NOT_WORTH: []}
    for path, title, worth in entries(landing, facts):
        said = f": {title}" if title else ""
        heading = NOT_WORTH if (worth or "").strip().lower() == "no" else FILED
        by[heading].append(f"- `{path}`{said}")
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
    filed = {found.finding: found for found in landing.filed}
    return tuple(
        seen_line(found)
        for review in landing.reviews
        if review.answered
        for found in pr_reviews.outside(review)
        if not (found.id in filed and filed[found.id].path)
        and not pr_reviews.mended(found, filed.get(found.id), fixed)
    )


def names_item(line: str, path: str) -> bool:
    """Whether a line names the item at `path`, and not another whose path starts the
    same."""
    return re.search(rf"(?<![\w./-]){re.escape(path)}(?![\w./-])", line) is not None


def placed(
    own: dict[Heading, Lines], steps: dict[Heading, list[str]]
) -> dict[Heading, Lines]:
    """The lines under `## Filed in the backlog` and `## Filed as not worth it`: the notes'
    own lines, then the step's. A notes line that names an item the step lists takes the
    place of the step's line, under the heading the item's `worth` gives."""
    lists = {heading: list(lines) for heading, lines in steps.items()}
    where = {
        line.split("`")[1]: heading
        for heading, lines in lists.items()
        for line in lines
    }
    slot = {
        line.split("`")[1]: at
        for lines in lists.values()
        for at, line in enumerate(lines)
    }
    kept: dict[Heading, list[str]] = {FILED: [], NOT_WORTH: []}
    taken: set[str] = set()
    for heading, lines in own.items():
        for line in lines:
            path = next((path for path in where if names_item(line, path)), None)
            if path is None:
                kept[heading].append(line)
            elif path in taken:
                lists[where[path]].append(line)
            else:
                taken.add(path)
                lists[where[path]][slot[path]] = line
    return {
        heading: (*kept[heading], *lists[heading]) for heading in (FILED, NOT_WORTH)
    }


def parts(
    record: Record, facts: Facts, fixed: str
) -> tuple[dict[Heading, list[str]], Lines]:
    """The step's item lines by heading, and its seen lines."""
    landing = record.landing or Landing()
    return items(landing, facts), seen(landing, fixed)
