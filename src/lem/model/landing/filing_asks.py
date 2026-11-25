"""Which defects `file` writes again, may judge, and asks Jev about (`land.cmd_file` on
`main`): the items it filed that the tip no longer holds, the defects `--same` and `--new` may
name, and those that get a file of their own with no word on them."""

from typing import TYPE_CHECKING

from lem.model.landing import items

if TYPE_CHECKING:
    from lem.model.landing import filing_place
    from lem.model.landing.filing_plan import Place, Waiting
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Finding


def gone_of(landing: Landing, shelf: filing_place.Shelf) -> tuple[str, ...]:
    """The items `file` filed that the tip no longer holds."""
    paths = (filed.path for filed in landing.filed if filed.disposition == "item")
    return tuple(path for path in paths if path and path not in shelf.paths)


def again_of(
    landing: Landing, shelf: filing_place.Shelf, *, again: bool
) -> tuple[str, ...]:
    """The places given again: each open item a defect was the same as that the tip no
    longer holds (`land.to_file` on `main` reads the open item's presence each time), and
    with `--again` each item `file` filed that the tip no longer holds."""
    paths = (filed.path for filed in landing.filed if filed.disposition == "same")
    left = tuple(path for path in paths if path and path not in shelf.paths)
    if not again:
        return left
    return (*left, *gone_of(landing, shelf), *refuted_of(landing, shelf))


def refuted_of(landing: Landing, shelf: filing_place.Shelf) -> tuple[str, ...]:
    """The open items an over-bar defect was the same as that say `worth: no` at the tip now:
    `--again` gives such a defect an item of its own that names the old one (propose's
    `item-refuted`)."""
    over = {
        finding.id
        for review in landing.reviews
        for finding in review.findings
        if finding.against == "over"
    }
    same = (
        one
        for one in landing.filed
        if one.disposition == "same" and one.finding in over
    )
    return tuple(
        one.path
        for one in same
        if one.path and items.worth_of(shelf.shelved, one.path) == "no"
    )


def free_of(left: Waiting, shelf: filing_place.Shelf) -> set[str]:
    """The waiting defects that get an item, with no open item of the tip that holds them:
    those `--same` and `--new` may name."""
    held = shelf.paths
    found = (finding for _, finding in left)
    return {finding.id for finding in found if free(finding, held)}


def free(finding: Finding, held: frozenset[str]) -> bool:
    """Whether the defect gets an item, with no open item of the tip that holds it."""
    return finding.against != "cheap" and finding.open not in held


type Asked = tuple[Finding, ...]


def asks_of(left: Waiting, places: list[Place], named: set[str]) -> Asked:
    """The defects Jev is asked about before anything is written: each that gets a file of
    its own, beside no old item, that `--same` and `--new` do not name."""
    found = [finding for _, finding in left]
    pairs = zip(found, places, strict=True)
    return tuple(finding for finding, place in pairs if asked(finding, place, named))


def asked(finding: Finding, place: Place, named: set[str]) -> bool:
    """Whether Jev is asked about the defect: it gets a file of its own, beside no old item,
    and `--same` and `--new` do not name it."""
    filed, write = place
    return write is not None and filed.cites is None and finding.id not in named
