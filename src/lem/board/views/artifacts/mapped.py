"""The parts of the map of a task's files: a file, a document with what hangs on it, a section,
a folder of working files, and the map whole."""

from lem.board.inputs.task.artifacts import Kind
from lem.board.views.artifacts.spots import Spot
from lem.records.base import Frozen


class Entry(Frozen, frozen=True, kw_only=True):
    """A file of the task: its path, its place, its kind, whether it comes first in its
    section (the plan), and the word of its link when it hangs on a document."""

    path: str
    spot: Spot
    kind: Kind
    first: bool = False
    label: str | None = None


class Hung(Frozen, frozen=True, kw_only=True):
    """A document and what hangs on it."""

    doc: Entry
    attached: tuple[Entry, ...] = ()


class Shelf(Frozen, frozen=True, kw_only=True):
    """A section of the map: its key, its name, its documents."""

    key: str
    name: str
    docs: tuple[Hung, ...] = ()


class Pile(Frozen, frozen=True, kw_only=True):
    """The working files of one folder; none for those at the top."""

    folder: str | None = None
    files: tuple[Entry, ...] = ()


class Map(Frozen, frozen=True, kw_only=True):
    """The map: its sections, its working files by folder, the number of documents and of
    working files."""

    sections: tuple[Shelf, ...]
    work: tuple[Pile, ...] = ()
    count: int = 0
    work_count: int = 0
