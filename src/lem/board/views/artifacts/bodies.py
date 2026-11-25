"""The parts of a file shown on the tab Artifacts that are no text of it: an HTML page in a frame,
a picture of the task's media, and a markdown file rendered.
"""

import hashlib
from typing import TYPE_CHECKING

from lem.board.inputs.task.artifacts import Body
from lem.board.inputs.task.cards import Picture
from lem.board.views.artifacts import kinds
from lem.board.views.artifacts.addresses import encoded, media_href, raw_href
from lem.board.views.artifacts.documents import document, forge_of
from lem.board.views.artifacts.spots import MEDIA_FOLDER

if TYPE_CHECKING:
    from lem.board.inputs.parts import Document
    from lem.board.views.artifacts.mapped import Entry
    from lem.board.views.world import Seen, World

KEY_LENGTH = 8


def pictured(world: World, slug: str, entry: Entry) -> Body | None:
    """An HTML page of the folder in a sandboxed frame, or a picture of its media; None for
    any other file."""
    where = f"It is at {entry.path} in the task’s folder."
    if entry.kind == kinds.HTML and not entry.first:
        return Body(frame=raw_href(world, slug, entry.path), where=where)
    if entry.kind == kinds.IMAGE and entry.path.startswith(MEDIA_FOLDER):
        return Body(picture=picture(world, slug, entry), where=where)
    return None


def picture(world: World, slug: str, entry: Entry) -> Picture:
    """A picture of the task's media, at its full size behind it."""
    name = encoded(entry.path.removeprefix(MEDIA_FOLDER))
    src = f"{media_href(world, slug)}{name}"
    return Picture(src=src, href=src, alt=entry.spot.title)


def rendered(world: World, seen: Seen, entry: Entry, text: str) -> Document:
    """A markdown file rendered, its links starting from its folder (the plan's from the
    repository's root)."""
    key = hashlib.sha256(entry.path.encode()).hexdigest()[:KEY_LENGTH]
    parent = None if entry.first else entry.path.rpartition("/")[0]
    media = media_href(world, seen.record.task.slug)
    forge = forge_of(seen.record)
    return document(f"art-{key}", text, forge, media=media, folder=parent or None)
