"""The search over every card of a workspace (Cmd-K): one row for each task and each backlog
item, in the order of the board."""

from typing import Literal

from lem.board.inputs.parts import Input
from lem.board.inputs.text import Href, Look, Plain


class Found(Input, frozen=True, kw_only=True):
    """A row of the search: a task or an item, its key (the slug, or the item's name), its
    title, its chip (`Waits for you · held`, `parked`, `landed 2026-11-25`, `Backlog ·
    undecided`), its look, where it goes, whether the task is open, and whether it opens in
    the panel."""

    kind: Literal["task", "item"]
    key: Plain
    title: Plain
    chip: Plain
    look: Look
    href: Href
    open: bool = False
    frame: bool = False


class Search(Input, frozen=True, kw_only=True):
    """The search box: its field's id (kept across a refresh) and its rows."""

    field: Plain
    rows: tuple[Found, ...] = ()
