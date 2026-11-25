"""The defects a review saw outside the change, as its record lists them under `outside`: each
gets its number (`r2.1`, by the attempt and its place) and keeps the review's call by the bar
(`land.defects_of` on `main`).

A call under the bar or cheap says why; an `open` item is a file of the backlog folder at the
base, which holds the same defect, so that no second item is filed for it.
"""

from lem.kernel.errors import Refusal
from lem.model.landing.item_names import slug_of
from lem.model.landing.review_said import Outside, Said, defects
from lem.records.landing.review import Finding

CALLED = (("under", "under the bar"), ("cheap", "cheap"))


def number(said: Said, place: int) -> str:
    """The number of the defect at `place` (from 1) of the attempt's list."""
    return f"r{said.attempt}.{place}"


def findings(said: Said) -> tuple[Finding, ...]:
    """The defects outside the change, each a finding of its number that `file` places."""
    return tuple(
        Finding(
            id=number(said, place),
            level="nit",
            where=found.where,
            title=found.title,
            what=found.what,
            against=found.against,
            why=found.why,
            open=found.open,
        )
        for place, found in enumerate(defects(said), 1)
    )


def one_refused(
    found: Outside, named: str, folder: str, at_base: frozenset[str]
) -> Refusal | None:
    """Why one defect of `outside`, numbered `named`, cannot be filed or named."""
    called = dict(CALLED)
    fix = "the review writes the defect as prompts/review.md, step 5, says"
    if not slug_of(found.title):
        why = f'the title of the defect {named} ("{found.title}") has no word for a file name'
        return Refusal("outside", why, fix)
    how = called.get(found.against)
    if how is not None and found.why is None:
        return Refusal(
            "outside",
            f'the defect {named} outside the change ("{found.title}") is {found.against}, '
            f"and has no `why`: one line that says why it is {how}",
            fix,
        )
    if found.open is not None and found.open not in at_base:
        return Refusal(
            "outside",
            f'`open` of the defect {named} outside the change ("{found.title}") is '
            f"{found.open!r}, which is no file of the backlog folder {folder} at the base",
            "`open` is the path of an item of the base that holds the same defect, as "
            "`backlog` in what `lem land read` printed gives it, or it is left out",
        )
    return None


def refused(said: Said, folder: str, at_base: frozenset[str]) -> Refusal | None:
    """The refusal of the first defect of `outside` that cannot be filed or named."""
    for place, found in enumerate(defects(said), 1):
        made = one_refused(found, number(said, place), folder, at_base)
        if made is not None:
            return made
    return None
