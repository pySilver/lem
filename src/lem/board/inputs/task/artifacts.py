"""The tab Artifacts of a task, `/HOST/WORKSPACE/tasks/SLUG/artifacts[/PATH/]`: the task's files
on one map, the same seven sections in every project and its working files, and the file
shown."""

from typing import Literal

from lem.board.inputs.parts import Document, Input, Link
from lem.board.inputs.task.cards import Picture
from lem.board.inputs.text import Href, Icon, Plain

# How a file is shown, by its kind.
type Kind = Literal[
    "markdown", "text", "json", "jsonl", "log", "html", "image", "binary"
]


class Doc(Input, frozen=True, kw_only=True):
    """A file on the map: its id (made from its path), its path and title, its icon, its
    address on the tab, whether it is the one shown, and the records and pictures that go with
    it."""

    id: Plain
    path: Plain
    title: Plain
    icon: Icon
    href: Href
    selected: bool = False
    attached: tuple[Link, ...] = ()


class Section(Input, frozen=True, kw_only=True):
    """A section of the map (The request, Criteria, The plan, The build, The checks, The review,
    The pull request): its key and name, its documents, and why it has none (`not yet: the lead
    writes it`)."""

    key: Plain
    name: Plain
    docs: tuple[Doc, ...] = ()
    empty: Plain | None = None


class Folder(Input, frozen=True, kw_only=True):
    """A folder of working files (`Pictures`, `Records with no document`, none for those at the
    top): its id and name, whether it is open (the file shown is in it), and its files."""

    id: Plain | None = None
    name: Plain | None = None
    open: bool = False
    docs: tuple[Doc, ...]


class Body(Input, frozen=True, kw_only=True):
    """The file as it is shown: rendered markdown, a JSON value or JSON lines marked up, the
    lines of a log or a text, an HTML page in a sandboxed frame, a picture; the tab that shows a
    record readable; why the board shows no text of it; and where the file is."""

    document: Document | None = None
    text: Plain | None = None
    lines: tuple[Plain, ...] = ()
    frame: Href | None = None
    picture: Picture | None = None
    record: Link | None = None
    said: Plain | None = None
    where: Plain


class Shown(Input, frozen=True, kw_only=True):
    """The file shown: its path, title and kind, its icon, its line (`pr.md · markdown · 1.2 KB
    · changed 08:32`), the address that opens an HTML page alone, and its body."""

    path: Plain
    title: Plain
    kind: Kind
    icon: Icon
    meta: Plain
    alone: Href | None = None
    body: Body


class Artifacts(Input, frozen=True, kw_only=True):
    """The tab: the sections, the working files and their count, the line under the map
    (`9 documents, read 16:00`, or what did not read), the file shown or the words in its place,
    whether a file is chosen in the address, and whether it is an HTML page the whole width
    shows."""

    sections: tuple[Section, ...]
    work: tuple[Folder, ...] = ()
    work_count: int = 0
    said: Plain
    problem: bool = False
    shown: Shown | None = None
    empty: Plain | None = None
    chosen: bool = False
    wide: bool = False
