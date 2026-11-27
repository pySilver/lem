"""The criteria of a plan, or of `criteria.md` in a task's folder (`criteria.parse` on `main`):

    ## Acceptance criteria

    Size: full, because the export gets a new column and two readers of it.

    1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has
       that text in its row.
       - test: `python3 -m unittest tests.test_export.GiftNote` in `tests/test_export.py`

`Size` names the track, `full` or `small`, with the reason after `because`. The criteria are
numbered 1, 2, 3 in order; under each come the steps of its case, its chart in a `mermaid` block,
and then its tests, or `- no test: REASON`. A chart of several criteria goes under
`## How it works`, after the section. The criteria of a feature go under a `### ` heading for each
of its parts and `### The whole feature` (`headings.py`). A section that does not have this form is
refused with the line.
"""

from lem.kernel.errors import Refusal
from lem.model.criteria import digest, headings, lines, section
from lem.model.criteria.draft import Draft, charted, taken
from lem.model.criteria.layout import Layout, layout_of
from lem.records.approvals import Size
from lem.records.base import Frozen
from lem.records.criterion import Criterion


class Sheet(Frozen, frozen=True, kw_only=True):
    """What a section says: the size and why, the criteria, How it works, and the mark of the
    criteria with their tests."""

    size: Size
    why: str
    criteria: tuple[Criterion, ...]
    how: str | None = None
    digest: str


def stepped(draft: Draft, layout: Layout, index: int) -> Draft:
    """The draft with line `index` of the section: a chart opens there, a line of words, or
    nothing (a blank line, a line of code)."""
    where = layout.where(index)
    if index in layout.charts:
        draft = charted(draft, layout.chart(index), where)
    row = layout.rows[index]
    if index in layout.code or not row.strip():
        return draft
    return taken(draft, row, where)


def refused(draft: Draft, name: str) -> Refusal | None:
    """Why a whole section is no set of criteria: no criterion, a fast track of more than one,
    or a criterion with a test and none."""
    found = draft.criteria
    if draft.size is None or not found:
        missing = "no criterion" if draft.size else "no Size line"
        return Refusal(lines.CODE, f"{name}: the section holds {missing}", section.FORM)
    if draft.size == "small" and len(found) != 1:
        return Refusal(
            lines.CODE,
            f"{name}: a task on the fast track has one criterion, and this one has "
            f"{len(found)}",
            "the task takes the standard track: Size: full, because WHY",
        )
    empty = headings.bare(draft.headings, len(found), draft.before)
    if empty is not None:
        return Refusal(
            lines.CODE,
            f"{name}: the heading {empty!r} has no criterion under it",
            "each heading has a criterion under it",
        )
    both = [one.number for one in found if one.tests and one.no_test]
    if both:
        return Refusal(
            lines.CODE,
            f"{name}: criterion {both[0]} names a test and says that it has none",
            "keep one of the two",
        )
    return None


def sheet_of(text: str, name: str) -> Sheet:
    """The criteria section of `text`, the file `name`, read."""
    layout = layout_of(text, name)
    draft = Draft()
    for index in layout.bounds:
        draft = stepped(draft, layout, index)
    refusal = refused(draft, name)
    if refusal is not None or draft.size is None:
        raise refusal or Refusal(lines.CODE, name, section.FORM)
    criteria = draft.criteria
    return Sheet(
        size=draft.size,
        why=draft.why,
        criteria=criteria,
        how=layout.how,
        digest=digest.of_tests(draft.size, criteria),
    )
