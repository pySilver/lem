"""A plan's criteria against the expected ones (`criteria.against` and `Task.no_small_plan` on
`main`).

Once criteria are approved, a plan's criteria are the newest approval's with each recorded
change applied, compared text for text and in order, each run of spaces as one; its `Size` is the
approved track, which only the owner's next approval changes. So the lead can neither reword,
drop nor add a criterion without the record saying so. A plan never puts a task on the fast
track: one plain change keeps its criterion in `criteria.md` and has no plan.
"""

from itertools import zip_longest
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.criteria import digest

if TYPE_CHECKING:
    from lem.model.criteria.read import Sheet
    from lem.model.decisions.changes import Changes

CODE = "criteria-differ"


def fix_of(slug: str) -> str:
    """The way on from a plan whose criteria are not the expected ones."""
    return (
        f"the plan's criteria are the approved ones with each recorded change (lem "
        f"decisions changes {slug} gives them), word for word, with only the test lines "
        f"added; a criterion the build changes, adds or removes is recorded first: lem "
        f"decisions criterion {slug} --changed N --was TEXT --now TEXT"
    )


def first_difference(expected: tuple[str, ...], sheet: Sheet, name: str) -> str | None:
    """The first criterion of the plan that is not the expected one, said, or None."""
    now = (digest.whole(one) for one in sheet.criteria)
    pairs = zip_longest(expected, now)
    for number, (want, have) in enumerate(pairs, start=1):
        if want is None:
            return f"criterion {number} of {name}, {have!r}, is not among the expected"
        if have is None:
            return f"{name} lacks criterion {number}, {want!r}, which is expected"
        if not digest.same(want, have):
            return (
                f"criterion {number} of {name} says {have!r}, and {want!r} is expected"
            )
    return None


def against(sheet: Sheet, changes: Changes, name: str, slug: str) -> Refusal | None:
    """Why the plan's criteria are not the expected ones, or None; with no approval, the
    plan's criteria are their one source."""
    approved = changes.approved
    if approved is None or changes.expected is None:
        return None
    if sheet.size != approved.size:
        return Refusal(
            "track",
            f"{name} says Size: {sheet.size}, and the owner approved Size: {approved.size}",
            f"a change of the track is the owner's only, by his approval again: lem "
            f"criteria approve {slug} --file FILE",
        )
    said = first_difference(changes.expected, sheet, name)
    return Refusal(CODE, said, fix_of(slug)) if said else None


def small_plan(sheet: Sheet, name: str) -> Refusal | None:
    """A plan that says Size: small is refused: one plain change takes the fast track, with no
    plan, and a fast-track task in a plan would land with none of the standard track's checks."""
    if sheet.size != "small":
        return None
    return Refusal(
        "small-plan",
        f"{name} says Size: small, and a plan never puts a task on the fast track",
        "a plan's criteria are the standard track's: Size: full, because WHY; one plain "
        'change keeps its criterion in criteria.md (stages/new.md, "The fast track")',
    )
