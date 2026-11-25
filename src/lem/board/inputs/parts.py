"""The parts every section of the board is made of: a moment as the page shows it, a link, a
chip, and the base of every input.

An input is frozen, takes its fields by keyword, refuses a key it does not know, and leaves a
default out of its JSON: the fixture of a page decodes strictly, so a field a view forgets to
fill is a failure, never a page that prints less.
"""

from typing import Literal

import msgspec

from lem.board.inputs.text import Href, Icon, Inline, Look, Markdown, Plain, Press
from lem.records.base import Moment


class Input(
    msgspec.Struct,
    frozen=True,
    kw_only=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
):
    """The base of every input of the board."""


class When(Input, frozen=True, kw_only=True):
    """A moment as the page prints it: the moment, its words at the page's minute (`20m`,
    `32m ago`, `15:40`), the hover that says what it is, and whether the browser's clock moves
    it on (`since` counts the length from it, `ago` the time since it)."""

    at: Moment
    shown: Plain
    title: Plain | None = None
    ticks: Literal["since", "ago"] | None = None


class Link(Input, frozen=True, kw_only=True):
    """A link: where it goes, its words, its hover, whether it opens a tab of its own (the
    forge), whether it opens in the task's panel, whether it is the page shown now, its icon,
    its look as a button (`Merge…` is a step that cannot be undone), and the row of the page it
    opens that it shows first (`dec-1`)."""

    href: Href
    label: Inline
    title: Plain | None = None
    out: bool = False
    frame: bool = False
    current: bool = False
    icon: Icon | None = None
    press: Press | None = None
    anchor: Plain | None = None


class Chip(Input, frozen=True, kw_only=True):
    """A small mark: its words (`**2** landed today`), its icon and look, its hover, whether it
    moves (a step that runs), where it links (a pull request), and an age after its words."""

    label: Inline
    icon: Icon | None = None
    look: Look | None = None
    title: Plain | None = None
    live: bool = False
    link: Link | None = None
    when: When | None = None


class Row(Input, frozen=True, kw_only=True):
    """One line of a card's list (a read of the criteria, a check, a review, an event): its
    stable id, its look and icon, its head in bold and the text after it, the lines under it,
    its hover, and the time at its right."""

    id: Plain
    look: Look
    icon: Icon
    head: Inline
    text: Inline | None = None
    subs: tuple[Inline, ...] = ()
    title: Plain | None = None
    time: Plain | None = None


class Document(Input, frozen=True, kw_only=True):
    """A markdown text the browser renders (a task's outcome, a breaker's document, the merge
    review, a criterion's chart): its id (`md-KEY-DIGEST`, which a refresh keeps while the text
    stays), the text, the address of the task's pictures it may show, and the folder its links
    start from."""

    id: Plain
    text: Markdown
    media: Href | None = None
    folder: Plain | None = None


class Note(Input, frozen=True, kw_only=True):
    """The result of an act of the owner, at the top of the page it came back to: its look
    and icon, its first word (`Running.`, `Done.`, `Not done.`, or none), and what it says."""

    look: Look
    icon: Icon
    word: Plain | None = None
    said: Inline
