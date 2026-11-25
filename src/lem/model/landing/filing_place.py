"""The place of one defect a review saw outside the change, by the review's call on it
(`land.cmd_file` on `main`; rule 6 of the builder's standing rules).

Over the bar it is an item with `worth: later`, under it one with `worth: no` that ends with the
review's reason, cheap a line of the pull request. One that an open item of the tip holds gets
no second file, but an over defect whose open item says `worth: no` gets a new `worth: later`
item that names the old one, which stays as it is. An item takes the first name that is free or
holds this very defect already (a second round saw it word for word, or a run cut off after its
commit).
"""

from typing import TYPE_CHECKING, Literal

from lem.model.landing import items
from lem.model.landing.item_names import Written, body, names_for
from lem.records.base import Frozen
from lem.records.landing.review import Filed

if TYPE_CHECKING:
    from lem.records.landing.review import Finding

type Worth = Literal["later", "no"]


class Shelf(Frozen, frozen=True, kw_only=True):
    """The backlog folder at the tip: the path of each file git has there, each item read,
    and the names taken on disk besides, a file git does not track among them. Only a file
    of the tip holds a defect; no name on disk is written over."""

    folder: str
    paths: frozenset[str] = frozenset()
    shelved: tuple[items.BacklogItem, ...] = ()
    taken: frozenset[str] = frozenset()


class Write(Frozen, frozen=True, kw_only=True):
    """An item to write: its path, its text, and the review round whose commit takes it."""

    path: str
    text: str
    round: int


class Seen(Frozen, frozen=True, kw_only=True):
    """Where a defect was seen: the review's round, the task, the day of the review, and the
    day of the filing."""

    round: int
    slug: str
    day: str
    today: str

    def line(self) -> str:
        """The item's line of where the defect was seen."""
        return (
            f"Seen outside the change by review round {self.round} of task {self.slug} "
            f"({self.day}); the base commit has it."
        )


def defect_of(finding: Finding) -> items.Defect:
    """The defect of a finding, as an item is written for it."""
    return items.Defect(where=finding.where, title=finding.title, what=finding.what)


def seen_line(finding: Finding, held: str | None = None) -> str:
    """The line of a finding no item of this filing holds, for the pull request: its place,
    its title, the review's call with its why, and the open item that holds it."""
    line = f"`{finding.where}`: {finding.title}"
    if finding.why:
        line = f"{line}; {finding.against}: {finding.why}"
    if held:
        line = f"{line}; an open item holds it, `{held}`"
    return line


def named(shelf: Shelf, defect: items.Defect, old: str | None) -> tuple[str, bool]:
    """The first name that holds the defect or is free, and whether it holds the defect.

    The old item a new one goes beside cannot hold it. `names_for` never runs out.
    """
    indexed = {one.path: one for one in shelf.shelved}
    occupied = shelf.paths | shelf.taken
    paths = map(f"{shelf.folder}/{{0}}".format, names_for(defect))
    while True:
        path = next(paths)
        held = path != old and items.holds(indexed.get(path), defect)
        if held or path not in occupied:
            return path, held


def itemized(
    finding: Finding, shelf: Shelf, seen: Seen, old: str | None
) -> tuple[Filed, Write | None]:
    """The item of a defect over or under the bar, and its file to write unless one holds it."""
    worth: Worth = "later" if finding.against == "over" else "no"
    path, there = named(shelf, defect_of(finding), old)
    if there:
        return Filed(
            finding=finding.id,
            disposition="item",
            path=path,
            worth=items.worth_of(shelf.shelved, path),
        ), None
    filed = Filed(
        finding=finding.id, disposition="item", path=path, worth=worth, cites=old
    )
    written = Written(
        worth=worth, added=seen.today, seen=seen.line(), why=finding.why, cites=old
    )
    return filed, Write(
        path=path, text=body(defect_of(finding), written), round=seen.round
    )
