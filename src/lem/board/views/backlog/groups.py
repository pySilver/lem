"""The backlog's groups and who holds an item (`BY_WORTH`, `worth_of`, `refuted`,
`worth_items`, `reviewer_items` and `undecided` of `board_model` on `main`).

The reviewer's items have a group of their own, the undecided ones first; every item of the
backlog folder, and each of the reviewer's items it decided against, is in the group of the
worth it gives itself. An open task that started from an item holds it.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

from lem.board.views.rule import ENDED

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from lem.board.inputs.backlog import Worth
    from lem.board.inputs.text import Look
    from lem.board.views.backlog_read import Entry, Shelved
    from lem.records.record import Record


class Group(NamedTuple):
    """A group of the backlog by worth: its key, its name, its look, and whether it stands
    back."""

    key: Worth
    name: str
    look: Look
    recessive: bool = False


UNSET: Worth = "unset"
BY_WORTH = (
    Group("yes", "Worth doing", "gate"),
    Group("later", "Later", "you"),
    Group(UNSET, "No verdict in the item", "quiet"),
    Group("no", "Decided against", "quiet", recessive=True),
)

# The worths an item may give itself; any other word, or none, is `unset`.
WORTHS: Mapping[str, Worth] = MappingProxyType(
    {group.key: group.key for group in BY_WORTH if group.key != UNSET}
)


def worth_of(entry: Entry) -> Worth:
    """The worth the item gives itself, `unset` for none or a word the board does not
    know."""
    return WORTHS.get(entry.worth or "", UNSET)


def refuted(entry: Entry) -> bool:
    """A reviewer's item that says `worth: no`: a proposal it decided against, kept so that no
    later night or retro raises it again. It waits for nobody."""
    return entry.reviewer and worth_of(entry) == "no"


def holder(records: Iterable[Record], path: str) -> Record | None:
    """The open task that started from the item at `path`, or None."""
    holding = (
        record
        for record in records
        if record.task.backlog_item == path and record.task.status not in ENDED
    )
    return next(holding, None)


def reviewer_entries(
    shelved: Shelved, records: tuple[Record, ...]
) -> tuple[tuple[Entry, Record | None], ...]:
    """The reviewer's items that are not refuted, each with the task that holds it: the
    undecided ones first, each part in the order of the read."""
    mine = [
        (entry, holder(records, entry.path))
        for entry in shelved.entries
        if entry.reviewer and not refuted(entry)
    ]
    loose = [pair for pair in mine if pair[1] is None]
    held = [pair for pair in mine if pair[1] is not None]
    return (*loose, *held)


def worth_entries(shelved: Shelved, key: Worth) -> tuple[Entry, ...]:
    """The items of the group `key`, in the order of the read: the backlog folder's, and in
    Decided against the reviewer's refuted ones too."""
    return tuple(
        entry
        for entry in shelved.entries
        if (not entry.reviewer or refuted(entry)) and worth_of(entry) == key
    )


def undecided(shelved: Shelved | None, records: tuple[Record, ...]) -> int | None:
    """How many of the reviewer's items no task holds, the count on the Backlog key; None with
    no read. A refuted item waits for nobody and is never counted."""
    if shelved is None:
        return None
    pairs = reviewer_entries(shelved, records)
    return sum(1 for _, held in pairs if held is None)
