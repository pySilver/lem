"""Parts of a breaker's card (`board_task.breaker_card` on `main`): its document, why the card
has none, and the link to the hand-over."""

from typing import TYPE_CHECKING

import msgspec

from lem.board.views.artifacts import addresses, documents
from lem.board.views.panel.review import artifact

if TYPE_CHECKING:
    from lem.board.inputs.parts import Document, Link
    from lem.board.views.world import Seen, World
    from lem.records.decisions import Breaker


def document_of(
    world: World, seen: Seen, found: Breaker, text: str | None
) -> Document | None:
    """The breaker's document, with the task's pictures; None when the folder lacks it."""
    if text is None:
        return None
    slug = seen.record.task.slug
    media = addresses.media_href(world, slug)
    forge = documents.forge_of(seen.record)
    return documents.document(f"breaker-{slug}-{found.id}", text, forge, media=media)


def missing(name: str) -> str:
    """Why the card shows no document."""
    return f"{name} is not in the task directory: the board has nothing to show of it."


def handoff(world: World, seen: Seen, found: Breaker) -> Link | None:
    """The link to the hand-over a fresh agent goes on from, while the folder holds it."""
    if found.handoff not in seen.files:
        return None
    link = artifact(world, seen.record.task.slug, found.handoff)
    title = "What a fresh agent goes on from"
    return msgspec.structs.replace(link, label="the handoff", title=title)
