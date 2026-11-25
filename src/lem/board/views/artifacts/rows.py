"""The map on the tab Artifacts (`board_task.art_tree` on `main`): each section with its
documents, each a row with its records and pictures as small links, an empty section with its
gray line, and the working files by folder, the folder of the file shown open."""

import hashlib
from typing import TYPE_CHECKING

from lem.board.inputs.parts import Link
from lem.board.inputs.task.artifacts import Doc, Folder, Section
from lem.board.views.artifacts.addresses import tab_href
from lem.board.views.artifacts.empty import empty_reason
from lem.board.views.artifacts.kinds import ICONS

if TYPE_CHECKING:
    from lem.board.views.artifacts.mapped import Entry, Pile, Shelf
    from lem.board.views.world import Seen, World

DOC_ID = 12
FOLDER_ID = 10


def link_of(world: World, slug: str, entry: Entry, shown: str | None) -> Link:
    """A record or a picture that hangs on a document's row."""
    href = tab_href(world, slug, entry.path)
    label = entry.label or "record"
    current = entry.path == shown
    return Link(href=href, label=label, title=entry.path, frame=True, current=current)


def doc_of(
    world: World,
    slug: str,
    entry: Entry,
    shown: str | None,
    hung: tuple[Entry, ...] = (),
) -> Doc:
    """A file's row on the map, with what hangs on it."""
    digest = hashlib.sha256(entry.path.encode()).hexdigest()[:DOC_ID]
    return Doc(
        id=f"af-{digest}",
        path=entry.path,
        title=entry.spot.title or entry.path,
        icon=ICONS[entry.kind],
        href=tab_href(world, slug, entry.path),
        selected=entry.path == shown,
        attached=tuple(link_of(world, slug, one, shown) for one in hung),
    )


def section_of(world: World, seen: Seen, shelf: Shelf, shown: str | None) -> Section:
    """A section of the map; with no document, the line of why."""
    slug = seen.record.task.slug
    docs = tuple(
        doc_of(world, slug, one.doc, shown, one.attached) for one in shelf.docs
    )
    empty = None if docs else empty_reason(seen.record, shelf.key)
    return Section(key=shelf.key, name=shelf.name, docs=docs, empty=empty)


def folder_of(world: World, slug: str, pile: Pile, shown: str | None) -> Folder:
    """A folder of working files, open when the file shown is in it; those at the top have no
    folder."""
    docs = tuple(doc_of(world, slug, one, shown) for one in pile.files)
    if pile.folder is None:
        return Folder(docs=docs)
    digest = hashlib.sha256(pile.folder.encode()).hexdigest()[:FOLDER_ID]
    opened = any(one.path == shown for one in pile.files)
    return Folder(id=f"as-{digest}", name=pile.folder, open=opened, docs=docs)
