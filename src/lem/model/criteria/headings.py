"""The headings of a feature's criteria: a `### ` heading for each part, and
`### The whole feature` for those only the whole feature meets
(`docs/plans/2026-11-27-a-feature-in-parts.md`, "The criteria of a part").

Once a section has a heading, each criterion is under one, each heading has a criterion, and no
heading comes twice. A criterion keeps the heading of its part, each run of spaces as one, and
none under the whole feature's heading.
"""

import re

HEADING = re.compile(r"^###\s+(\S.*)$")
# The heading of the group that only the whole feature meets, in any case.
WHOLE = "the whole feature"
FIX = (
    "in criteria with headings, each criterion is under one ### heading, one for each part "
    "and ### The whole feature, each heading once and with a criterion under it"
)


def bare(headings: tuple[str, ...], count: int, before: int) -> str | None:
    """The newest of `headings` when no criterion came under it, or None: `count` criteria
    so far, `before` of them before that heading."""
    if headings and count == before:
        return headings[-1]
    return None


def wrong(
    headings: tuple[str, ...], count: int, before: int, heading: str
) -> str | None:
    """Why `heading` may not come after `headings` and `count` criteria, or None."""
    if count and not headings:
        return "criterion 1 is under no heading"
    empty = bare(headings, count, before)
    if empty is not None:
        return f"the heading {empty!r} has no criterion under it"
    if heading.casefold() in {one.casefold() for one in headings}:
        return f"the heading {heading!r} comes twice"
    return None


def part_of(heading: str) -> str | None:
    """The part the criteria under `heading` belong to: None for the whole feature's."""
    return None if heading.casefold() == WHOLE else heading
