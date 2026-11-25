"""The parts every section of the board is made of: a moment as the page shows it, a link, a
chip, and the base of every input.

An input is frozen, takes its fields by keyword, refuses a key it does not know, and leaves a
default out of its JSON: the fixture of a page decodes strictly, so a field a view forgets to
fill is a failure, never a page that prints less.
"""

from datetime import datetime
from typing import Annotated, Literal

import msgspec

from lem.board.inputs.text import Href, Icon, Inline, Look, Markdown, Plain

# A moment with its zone, as every record holds it.
type Moment = Annotated[datetime, msgspec.Meta(tz=True)]


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
    forge), whether it opens in the task's panel, and whether it is the page shown now."""

    href: Href
    label: Inline
    title: Plain | None = None
    out: bool = False
    frame: bool = False
    current: bool = False


class Chip(Input, frozen=True, kw_only=True):
    """A small mark: its words, its icon and look, its hover, whether it moves (a step that
    runs), and where it links when it does (a pull request)."""

    label: Plain
    icon: Icon | None = None
    look: Look | None = None
    title: Plain | None = None
    live: bool = False
    link: Link | None = None


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
