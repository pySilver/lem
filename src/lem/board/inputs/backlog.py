"""The view Backlog, `/HOST/WORKSPACE/backlog`: the reviewer's items, then the backlog's items
by the worth each gives itself, with the filter of the address and its chips."""

from typing import Literal

from lem.board.inputs.forms import ActForm
from lem.board.inputs.parts import Chip, Document, Input, Link
from lem.board.inputs.text import Href, Inline, Look, Plain

# The worth an item gives itself, and `unset` for one that gives none.
type Worth = Literal["yes", "later", "unset", "no"]


class Added(Input, frozen=True, kw_only=True):
    """Who added an item and where (`added by Ann on 2026-11-24, in task fix-the-login`): the
    words, the task it came from, and the words after the task (`, in pull request #38`)."""

    said: Plain
    task: Link | None = None
    after: Plain | None = None


class Holds(Input, frozen=True, kw_only=True):
    """What the owner may do with an item: the task that builds it and the words after it
    (`(parked) builds this item.`); else the start and the drop (where the page may act) with
    their note; else the line he types in a session, which a button copies; or why no line
    would keep its path."""

    held_by: Link | None = None
    held: Plain | None = None
    start: ActForm | None = None
    drop: ActForm | None = None
    note: Plain | None = None
    typed: Plain | None = None
    bad: Plain | None = None


class Entry(Input, frozen=True, kw_only=True):
    """An item: its key and path, its title, its worth, its tags (`held by SLUG`,
    `undecided`, `new, not committed`, `today`), the place in the code it names and why that
    place no longer resolves, whether it is new, who added it, its text, and what the owner may
    do with it."""

    key: Plain
    path: Plain
    title: Inline
    worth: Worth
    tags: tuple[Chip, ...] = ()
    where: Plain
    where_problem: Plain | None = None
    new: bool = False
    added: Added | None = None
    body: Document | None = None
    holds: Holds


class Shelf(Input, frozen=True, kw_only=True):
    """A group of items (the reviewer's, `Worth doing`, `Later`, `No verdict in the item`,
    `Decided against`): its key, its look, its name and hover, whether it stands back, and its
    items."""

    key: Plain
    look: Look
    name: Plain
    title: Plain | None = None
    recessive: bool = False
    entries: tuple[Entry, ...]


class Filter(Input, frozen=True, kw_only=True):
    """A chip of the filter: its key and the value it sets, its words and look, how many items
    it keeps, whether it is on, its address (a second press turns it off), and its hover."""

    key: Plain
    shown: Plain
    label: Plain
    look: Look | None = None
    count: int
    on: bool = False
    href: Href
    title: Plain


class Backlog(Input, frozen=True, kw_only=True):
    """The view: the line of what it holds (`2 items in docs/backlog · 3 of the reviewer...`),
    the words of the filter's box, the address that reads the backlog again, the chip of every
    item and the chips of the filter, the shelves, and the words when it did not read or holds
    nothing."""

    summary: Plain
    query: Plain = ""
    read_again: Href
    every: Filter
    filters: tuple[Filter, ...] = ()
    shelves: tuple[Shelf, ...] = ()
    empty: Plain | None = None
