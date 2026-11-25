"""The parts of the card of the criteria's wait that are no rule: the criteria as the task's
session wrote them, rendered with the task's pictures, and the way back to its Overview that a
phone's sheet shows."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import task_href
from lem.board.inputs.parts import Link
from lem.board.views.artifacts.addresses import media_href
from lem.board.views.artifacts.documents import document, forge_of

if TYPE_CHECKING:
    from lem.board.inputs.parts import Document
    from lem.board.views.world import Seen, World


def written(world: World, seen: Seen, text: str | None) -> Document | None:
    """The criteria as the task's session wrote them, or None before it did."""
    if text is None:
        return None
    slug = seen.record.task.slug
    media = media_href(world, slug)
    return document(f"waiting-{slug}", text, forge_of(seen.record), media=media)


def back(world: World, seen: Seen) -> Link:
    """The way back to the task's Overview, which a phone's sheet shows."""
    viewer = world.viewer
    href = task_href(viewer.base, seen.record.task.slug, None, viewer.view)
    return Link(href=href, label="Back", frame=True)
