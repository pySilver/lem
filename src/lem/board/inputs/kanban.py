"""The input of the kanban's template: its columns and their cards, as the template prints
them, and the page's addresses and version (the slice of `slice-board`; `board-inputs` owns the
form of every section)."""

import msgspec


class Card(msgspec.Struct, frozen=True, kw_only=True):
    """A task on the kanban: its slug, the first line of what was asked, its status, its line
    (the status, and the kind of what holds it: `owner`, `breaker`, `blocked`, `parked`,
    `release`), and since when."""

    slug: str
    ask: str
    status: str
    line: str
    since: str


class Lane(msgspec.Struct, frozen=True, kw_only=True):
    """A column: who acts (its key and its look), its title, its line when empty, its cards."""

    key: str
    actor: str
    title: str
    empty: str
    cards: tuple[Card, ...] = ()


class Kanban(msgspec.Struct, frozen=True, kw_only=True):
    """The kanban of one workspace: the page's title, the machine and workspace of its
    address, where its assets and its stream are, the version it shows, and its columns."""

    title: str
    host: str
    workspace: str
    assets: str
    stream: str
    version: str
    lanes: tuple[Lane, ...]
