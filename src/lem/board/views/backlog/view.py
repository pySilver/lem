"""The view Backlog, `/HOST/WORKSPACE/backlog` (`board_pages.backlog_page` on `main`): the
reviewer's items, the undecided ones first, then the backlog's items by the worth each gives
itself, the reviewer's refuted ones under Decided against; the line of what it holds, the
filter of the address and its chips."""

from typing import TYPE_CHECKING

from lem.board.inputs.backlog import Backlog, Shelf
from lem.board.inputs.layout import KeyGroup, Keys
from lem.board.views.backlog import filters, groups
from lem.board.views.backlog.entry import entry_of
from lem.board.views.backlog.summary import summary_of

if TYPE_CHECKING:
    from lem.board.views.backlog.wanted import Wanted
    from lem.board.views.backlog_read import Shelved
    from lem.board.views.world import World
    from lem.records.record import Record

KEYS = Keys(
    id="backlog-keys",
    groups=(
        KeyGroup(keys=("/",), word="filter"),
        KeyGroup(keys=("J", "K"), word="move"),
        KeyGroup(keys=("Enter",), word="open or close"),
        KeyGroup(keys=("R",), word="read again"),
    ),
)
REVIEWER = (
    "What the night and the retro proposed and the reviewer passed, in {folder}: start a "
    "task or drop it"
)
NOT_READ = "The backlog was not read: {why}."
NONE = (
    "No item in {folder} or {reviewer}. The polish pass of a landing files items, /backlog "
    "adds one, and the reviewer of the night's and the retro's proposals writes its own."
)


def backlog(world: World, want: Wanted) -> Backlog:
    """The Backlog view of the world, with the filter `want` of its address."""
    base = world.viewer.base
    shelved = world.backlog
    records = tuple(seen.record for seen in world.tasks)
    found = shelved.entries if shelved else ()
    return Backlog(
        summary=summary_of(world, records) if shelved else "",
        query=want.words,
        read_again=f"{base}/backlog?read=1",
        every=filters.every(found, want, base),
        filters=filters.chips(found, want, base),
        shelves=shelves_of(world, records) if shelved else (),
        empty=empty_of(shelved),
    )


def shelves_of(world: World, records: tuple[Record, ...]) -> tuple[Shelf, ...]:
    """The groups of items: the reviewer's, then each worth that has an item."""
    shelved = world.backlog
    if shelved is None:
        return ()
    reviewer = reviewer_shelf(world, records, shelved)
    by_worth = worth_shelves(world, records, shelved)
    return (reviewer, *by_worth) if reviewer else by_worth


def reviewer_shelf(
    world: World, records: tuple[Record, ...], shelved: Shelved
) -> Shelf | None:
    """The reviewer's items that are not refuted, the undecided ones first; None with
    none."""
    pairs = groups.reviewer_entries(shelved, records)
    if not pairs:
        return None
    return Shelf(
        key="reviewer",
        look="you",
        name="The reviewer's items",
        title=REVIEWER.format(folder=shelved.reviewer),
        entries=tuple(entry_of(world, records, entry) for entry, _ in pairs),
    )


def worth_shelves(
    world: World, records: tuple[Record, ...], shelved: Shelved
) -> tuple[Shelf, ...]:
    """A group for each worth that has an item, in the order of `groups.BY_WORTH`."""
    kept = (
        (group, groups.worth_entries(shelved, group.key)) for group in groups.BY_WORTH
    )
    return tuple(
        Shelf(
            key=group.key,
            look=group.look,
            name=group.name,
            recessive=group.recessive,
            entries=tuple(entry_of(world, records, entry) for entry in found),
        )
        for group, found in kept
        if found
    )


def empty_of(shelved: Shelved | None) -> str | None:
    """The words of a backlog that did not read or holds nothing; None for one with items."""
    if shelved is None:
        return NOT_READ.format(why="the status bar says why")
    if shelved.problem:
        return NOT_READ.format(why=shelved.problem)
    if shelved.entries:
        return None
    return NONE.format(folder=shelved.folder, reviewer=shelved.reviewer)
